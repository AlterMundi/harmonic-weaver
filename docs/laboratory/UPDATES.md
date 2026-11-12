# The shared laboratory and its updates

The maintained source is [AlterMundi/harmonic-weaver](https://github.com/AlterMundi/harmonic-weaver), on `main`. The ordinary laboratory includes the body view, named camera/orientation controls, movement tutorial, fullscreen dancing, volume response, recording setup and the **Rostro** instrument. These features are not an Amapola-only frontend or a separate everyday installation.

The native body/audio companion sources are [AlterMundi/HarMoCAP](https://github.com/AlterMundi/HarMoCAP) and [AlterMundi/harmonic-shaper](https://github.com/AlterMundi/harmonic-shaper). Keep the required companion APIs installed as described in [RUNNING](RUNNING.md); a Weaver source pull does not secretly rewrite those separate checkouts.

## Update an existing installation

Finish recordings and retain/export unsaved browser research trials before updating or restarting. Keep local source changes and machine settings; never reset a divergent checkout to obtain an update. From the existing Weaver checkout, use a fast-forward update of the canonical shared source:

```sh
git pull --ff-only https://github.com/AlterMundi/harmonic-weaver.git main
```

If Git reports local commits/conflicts, stop there and integrate the selected shared changes while preserving them. This command does not overwrite a locally maintained calibration line such as Amapola's. It does not change personal remotes or update anybody else's computer.

Then use the same existing `scripts/start-laboratory.sh` command with the machine's chosen audio device, tracking model and data directory. The launcher refreshes UI dependencies when `package.json`, its lockfile or the Node runtime ABI changes, including installations that already have `node_modules`. A failed refresh stops before building/starting audio; a successful unchanged installation reuses its dependencies. The ordinary build includes the pinned facial model/WASM and verifies their hashes. First installation/model preparation can require network access.

The served entry HTML is marked `Cache-Control: no-store`. Opening/reloading the updated laboratory obtains its current entry and versioned bundles. An already open performance or research trial is not automatically reloaded, interrupted or silently retuned. Restart the existing server to load backend changes, then reload the browser when ready.

## Source and personal data are different

New users receive the shared features from the maintained source and its build. Camera permission, the selected device, personal resting reference, presets, recordings, folders, Drive account/grants and research responses belong to their installation/browser. Updating does not publish or copy Sai's camera frames, private files, accounts or unsaved session. See [running the laboratory](RUNNING.md), [camera scope](CAMERAS.md), [recording setup](RECORDING_SETUP.md) and [Rostro](face/README.md).

An old downloaded copy or an old separately running server does not update itself from GitHub. This workflow is a source update and ordinary launch, not a background auto-updater or a newly published public webcam service.

## macOS receiving

Use the shared [native receiving guide](integrations/MACOS.md), exact CoreAudio
selection and companion Spatializer update. A source pull or Linux test does
not establish native audio/tracking acceptance. Existing Mac data/permissions
and local changes remain with their receiving operator.

## Sai source adoption

The [contribution audit](integrations/SAI_CONTRIBUTIONS.md) records shared UI work
and the companion named-camera correction. The Mac receiving cutoff now includes
HarMoCAP `4d56e4d`; previous source inclusion does not claim device acceptance.
