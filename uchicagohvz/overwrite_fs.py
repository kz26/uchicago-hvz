from django.core.files.storage import FileSystemStorage

class OverwriteFileSystemStorage(FileSystemStorage):

	def _save(self, name, content):
		if self.exists(name):
			self.delete(name)
		return super(OverwriteFileSystemStorage, self)._save(name, content)

	def get_available_name(self, name):
		return name
