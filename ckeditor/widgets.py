from django import forms

class CKEditorArea(forms.Textarea):
	class Media:
		js = ('js/vendor/ckeditor/ckeditor.js', 'js/vendor/ckeditor/adapters/jquery.js', 'js/ckEditorActivate.js')

	def __init__(self, *args, **kwargs):
		attrs = kwargs.get('attrs', {'class': 'ckeditor'})
		kwargs['attrs'] = attrs
		super(CKEditorArea, self).__init__(*args, **kwargs)

