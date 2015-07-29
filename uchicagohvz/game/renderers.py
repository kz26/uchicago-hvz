from rest_framework import renderers

class MailingListRenderer(renderers.BaseRenderer):
    media_type = 'text/plain'
    format = 'txt'

    def render(self, data, media_type=None, renderer_context=None, *args, **kwargs):
        return data.encode(self.charset)