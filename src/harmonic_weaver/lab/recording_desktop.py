"""Native GTK/GIO adapter. Run with the desktop's system Python, never a shell.

Only the picker grants destinations. OAuth remains in the desktop keyring.
The JSON protocol never returns credentials or reads arbitrary chosen source files.
"""
import configparser
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
from urllib.parse import unquote, urlsplit


def cloud_account(uri):
    parsed=urlsplit(uri)
    if parsed.scheme!='google-drive' or parsed.query or parsed.fragment:
        raise ValueError('Elegí una carpeta de Google Drive.')
    return unquote(parsed.netloc).casefold()


def drive_status(expected):
    config=configparser.ConfigParser(interpolation=None)
    config.read(Path.home()/'.config/goa-1.0/accounts.conf')
    found=any(config.get(s,'Provider',fallback='')=='google' and
              config.get(s,'Identity',fallback='').casefold()==expected.casefold() and
              config.getboolean(s,'FilesEnabled',fallback=True) and
              not config.getboolean(s,'FilesDisabled',fallback=False) for s in config.sections())
    return {'account':expected,'account_available':bool(expected and found),
            'connect_available':any(shutil.which(x) for x in ['gnome-online-accounts-gtk','cinnamon-settings','gnome-control-center'])}


def gio():
    import gi
    gi.require_version('Gio','2.0')
    from gi.repository import Gio
    return Gio


def folder_info(uri,kind,expected):
    Gio=gio()
    if kind=='drive':
        if not expected or cloud_account(uri)!=expected.casefold():
            raise ValueError('La carpeta debe pertenecer a la cuenta institucional elegida.')
    elif urlsplit(uri).scheme!='file' or '/gvfs/google-drive:' in unquote(uri):
        raise ValueError('Para guardar en Drive, elegí Google Drive como destino.')
    folder=Gio.File.new_for_uri(uri)
    info=folder.query_info('standard::type,standard::display-name,access::can-write',Gio.FileQueryInfoFlags.NONE,None)
    if info.get_file_type()!=Gio.FileType.DIRECTORY:raise ValueError('Elegí una carpeta.')
    if info.has_attribute('access::can-write') and not info.get_attribute_boolean('access::can-write'):
        raise ValueError('Esta carpeta no permite guardar archivos.')
    return folder,info


def pick(kind,expected):
    import gi
    gi.require_version('Gtk','3.0')
    from gi.repository import Gtk
    dialog=Gtk.FileChooserDialog(title='Elegir carpeta para las tomas',action=Gtk.FileChooserAction.SELECT_FOLDER)
    dialog.add_buttons('Cancelar',Gtk.ResponseType.CANCEL,'Elegir carpeta',Gtk.ResponseType.OK)
    dialog.set_local_only(kind!='drive')
    try:
        result=dialog.run()
        if result!=Gtk.ResponseType.OK:return {'status':'cancelled'}
        uri=dialog.get_uri();folder,info=folder_info(uri,kind,expected)
        return {'status':'selected','uri':folder.get_uri(),'label':info.get_display_name()}
    finally:dialog.destroy()


def transfer(request,verify=False):
    Gio=gio();kind=request['kind'];folder,_=folder_info(request['uri'],kind,request.get('account',''))
    name=request['filename']
    if Path(name).name!=name or not name.startswith('HarmoCap-'):
        raise ValueError('Nombre de salida inválido.')
    destination=folder.get_child_for_display_name(name)
    expected=request['sha256']
    if not verify and not destination.query_exists(None):
        source=Gio.File.new_for_path(request['source'])
        source.copy(destination,Gio.FileCopyFlags.NOFOLLOW_SYMLINKS,None,None,None)
    stream=destination.read(None);digest=hashlib.sha256();size=0
    try:
        while True:
            data=stream.read_bytes(1024*1024,None).get_data()
            if not data:break
            digest.update(data);size+=len(data)
    finally:stream.close(None)
    if digest.hexdigest()!=expected or size!=request['size']:
        raise ValueError('La copia no coincide con el original; conservamos ambos para revisar.')
    info=destination.query_info('standard::name',Gio.FileQueryInfoFlags.NONE,None)
    return {'status':'verified','uri':folder.get_child(info.get_name()).get_uri(),'size':size,'sha256':digest.hexdigest()}


def main():
    request=json.load(sys.stdin);action=request['action']
    if action=='status':return drive_status(request.get('account',''))
    if action=='pick':return pick(request['kind'],request.get('account',''))
    if action=='connect':
        command=next((c for c in [['gnome-online-accounts-gtk'],['cinnamon-settings','online-accounts'],['gnome-control-center','online-accounts']] if shutil.which(c[0])),None)
        if not command:raise ValueError('Abrí Cuentas en línea desde la configuración de esta computadora.')
        subprocess.Popen(command,stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,start_new_session=True)
        return {'status':'opened','account':request.get('account','')}
    if action in ('copy','verify'):return transfer(request,verify=action=='verify')
    raise ValueError('Operación de destino desconocida.')


if __name__=='__main__':
    try:print(json.dumps(main(),ensure_ascii=False))
    except Exception as exc:
        # Provider exceptions can include private URLs. Keep them out of UI/logs.
        message=str(exc) if isinstance(exc,ValueError) else 'No se pudo confirmar la operación en la carpeta. Revisá la conexión y sus permisos.'
        print(json.dumps({'status':'error','error':message},ensure_ascii=False));sys.exit(1)
