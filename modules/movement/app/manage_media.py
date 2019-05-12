import os, uuid, sys
from azure.storage.blob import BlockBlobService, PublicAccess
import keymanager

account_name = keymanager.MODULE_BLOB_USERNAME
account_key = keymanager.MODULE_BLOB_KEY

## ManageMedia creates an object that can handle uploading and downloading of photos and videos to and from
## Azure blob storage
class ManageMedia(object):

	def __init__(self, type: str):
		# Account identity
		self.account_name = account_name
		self.account_key = account_key
		# Create block blob service object
		self.blob_service = BlockBlobService(self.account_name, self.account_key)
		# Setup container
		self.container = type
		# Set local paths
		self.upload_folder = type
		self.download_folder = "downloads"
		# Set permission to access
		self.blob_service.set_container_acl(self.container, public_access=PublicAccess.Container)
		# Set container url
		self.container_url = "https://" + self.account_name + ".blob.core.windows.net/" + self.container + "/"
		print("ManageMedia object created.")


	## Upload selected videos by passing a list, or all videos by passing "all"
	## return: list of urls
	def upload(self, name_list: [str]):
		try:
			url_list = []
			number = 0
			if name_list == "all":
				name_list = os.listdir(self.upload_folder)
			for i, name in enumerate(name_list, 1):
				url_list.append((self.container_url + name))
				file_path = os.path.join(self.upload_folder, name)
				self.blob_service.create_blob_from_path(self.container, name, file_path)
				number = i
				print("Uploaded: " + file_path
			print("Number of uploads: " + str(number))
			return url_list
		except Exception as e:
			print(e)

	## Download selected videos by passing a list, or all videos by passing "all"
	## return: list of urls
	def download(self, name_list: []):
		try:
			url_list = []
			number = 0
			if name_list == "all":
				name_list = os.listdir(self.download_folder)
			for i, name in enumerate(name_list, 1):
				url_list.append(self.container_url + name)
				file_path = os.path.join(self.download_folder, name)
				self.blob_service.get_blob_to_path(self.container, name, file_path)
				number = i
				print("Downloaded: " + file_path)
				print("Number of downloads: " + str(number))
			return url_list
		except Exception as e:
			print(e)

	## Delete selected local videos by passing a list, or all videos by passing "all"
	## Select which folder to delete in by passing folder name
	## return: list of urls
	def delete_local(self, folder: str, name_list: [str]):
		try:
			if folder == self.upload_folder or folder == self.download_folder:
				url_list = []
				number = 0
				if name_list == "all":
					name_list = os.listdir(folder)
				for i, name in enumerate(name_list, 1):
					url_list.append(self.container_url + name)
					file_path = os.path.join(folder, name)
					os.remove(file_path)
					number = i
					print("File deleted: " + file_path)
				print("Number of deletes: " + str(number))
				return url_list
			else:
				print("ERROR: folder must be \"" + self.upload_folder + " or " + self.download_folder + ".")
		except Exception as e:
			print(e)

	## Delete selected local videos by passing a list, or all videos by passing "all"
	## return: list of urls
	def delete_blob(self, name_list: []):
		try:
			url_list = []
			number = 0
			if name_list == "all":
				blob_list = self.blob_service.list_blobs(self.container)
				for blob in blob_list:
					url_list.append(self.container_url + blob.name)
				self.blob_service.delete_container(self.container)
				self.blob_service.create_container(self.container)
				print("All blobs deleted.")
				print("Number of deletes: " + str(len(blob_list)))
				return url_list
			else:
				for i, name in enumerate(name_list, 1):
					url_list.append(self.container_url + name)
					self.blob_service.delete_blob(self.container, name)	
					number = i				
					print("Blob deleted: " + name)
				print("Number of deletes: " + str(number))
				return url_list
		except Exception as e:
			print(e)

	## List local videos.
	## Select folder to list by passing folder name
	## return: list of urls
	def list_local(self, folder: str):
		try:
			if folder == self.upload_folder or folder == self.download_folder:
				url_list = []
				name_list = os.listdir(folder)
				number = 0
				print("Items in " + folder)
				for i, name in enumerate(name_list, 1):
					url_list.append(self.container_url + name)
					number = i
					print(name)
				print("Number of items: " + str(number))
				return url_list
			else:
				print("ERROR: folder must be \"" + self.upload_folder + " or " + self.download_folder + ".")
		except Exception as e:
			print(e)

	## List blobs in blob storage.
	## return: list of urls
	def list_blob(self):
		try:
			url_list = []
			blob_list = self.blob_service.list_blobs(self.container)
			number = 0
			print("Items in " + self.container)
			for i, blob in enumerate(blob_list, 1):
				url = self.container_url + blob.name
				url_list.append(url)
				number = i
				print(blob.name + "        " + url)
			print("Number of blobs: " + str(number))
			return url_list
		except Exception as e:
			print(e)