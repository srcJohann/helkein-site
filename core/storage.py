from django.core.files.storage import FileSystemStorage
from django.conf import settings
from cryptography.fernet import Fernet
from django.core.files.base import ContentFile
import io

class EncryptedFileSystemStorage(FileSystemStorage):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fernet = Fernet(settings.ENCRYPTION_KEY)

    def _save(self, name, content):
        # Read the content
        if hasattr(content, 'read'):
            data = content.read()
        else:
            data = content
            
        # Encrypt the data
        encrypted_data = self.fernet.encrypt(data)
        
        # Create a new file-like object with encrypted data
        # We use ContentFile to ensure it behaves like a Django file
        encrypted_content = ContentFile(encrypted_data)
        return super()._save(name, encrypted_content)

    def _open(self, name, mode='rb'):
        # Open the file using the parent class
        f = super()._open(name, mode)
        encrypted_data = f.read()
        
        try:
            # Decrypt the data
            decrypted_data = self.fernet.decrypt(encrypted_data)
            return ContentFile(decrypted_data)
        except Exception:
            # If decryption fails, it might be an unencrypted file (legacy)
            return ContentFile(encrypted_data)
