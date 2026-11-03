"""Fresh entry HTML for the existing laboratory; versioned bundles stay reusable."""
from fastapi.staticfiles import StaticFiles


class LaboratoryUIFiles(StaticFiles):
    async def get_response(self, path, scope):
        response = await super().get_response(path, scope)
        if path in {'', '.', '/', 'index.html'} or response.headers.get('content-type', '').startswith('text/html'):
            response.headers['Cache-Control'] = 'no-store'
        return response
