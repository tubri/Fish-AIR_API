"""
The purpose of this script is to upload a series of images and metadata to the server.
It does so by reading a user-provided CSV file containing information about the images and metadata to be uploaded.

When running the script, it performs the following steps in order:

1. Asks the user if they need to create a new Batch.
2. If the user needs to create a Batch, collects the relevant Batch information and creates the Batch.
3. Reads the user-provided CSV file containing the information of the images to be uploaded.
4. Processes each image and metadata line by line from the CSV file.
5. Attempts to upload the images and metadata while handling any errors that may occur.
6. Writes the processing results (success or failure) to an output CSV file.

Notes:
    - If there are errors during the upload process, the script records the error information in the output file.
    - The output file name includes a timestamp to distinguish between different run results.
"""

import argparse

import requests
import csv, datetime, sys

# Define the API URL as a global constant
API_BASE_URL = 'https://fishair.org/api/'
# API_BASE_URL = 'http://127.0.0.1:8000/'
timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
OUTPUT_FILE = f'uploadimage_with_responses_{timestamp}.csv'

# create a new batch
def create_batch(batch_info, api_key, file, image_info_path):
    # read images and associated metadata from arg - image list file
    with open(image_info_path, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        fieldnames = reader.fieldnames
        if 'errorMessage' not in fieldnames:
            fieldnames.append('errorMessage')

        #API request: create a new batch
        headers = {'x-api-key': api_key}
        try:
            if file:
                with open(file, 'rb') as f:
                    file = {'supplementFile': f}
                    response = requests.post(API_BASE_URL + "batch", headers=headers, data=batch_info, files=file)
            else:
                response = requests.post(API_BASE_URL + "batch", headers=headers, data=batch_info)

            #error handling, write image list and error message to OUTPUT_FILE
            if response.status_code != 200:
                print(response.text)
                with open(OUTPUT_FILE, 'a', newline='') as output_csvfile:
                    writer = csv.DictWriter(output_csvfile, fieldnames=fieldnames)
                    writer.writeheader()
                    for row in reader:
                        row['errorMessage'] = "generated batch failed:" + response.text
                        writer.writerow(row)
                sys.exit()
            else:
                batch_ark_id = response.json()['ark_id']
                print("your new batch ARK ID is: ",batch_ark_id)
                return batch_ark_id
        except Exception as e:
            with open(OUTPUT_FILE, 'a', newline='') as output_csvfile:
                print(str(e))
                writer = csv.DictWriter(output_csvfile, fieldnames=fieldnames)
                writer.writeheader()
                for row in reader:
                    row['errorMessage'] = "generated batch failed:" + str(e)
                    writer.writerow(row)
                sys.exit()

#upload images and metadata to the batch
def upload_images(batch_ark_id, image_info_path, api_key):
    # read images and associated metadata from arg - image list file
    with open(image_info_path, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        fieldnames = reader.fieldnames
        if 'ARKID' not in fieldnames:
            fieldnames.append('ARKID')
        if 'errorMessage' not in fieldnames:
            fieldnames.append('errorMessage')
        if 'BatchARKID' not in fieldnames:
            fieldnames.append('batchARKID')
        # write image list & returned ark id & errors to OUTPUT_FILE
        with open(OUTPUT_FILE, 'a', newline='') as output_csvfile:
            writer = csv.DictWriter(output_csvfile, fieldnames=fieldnames)
            writer.writeheader()

            # API request: upload images and metadata
            for row in reader:
                try:
                    image_path = row['imageLocalPath']
                    row["batchARKID"] = batch_ark_id

                    with open(image_path, 'rb') as f:
                        image_data = {'file': f}

                        headers = {'x-api-key': api_key}
                        response = requests.post(API_BASE_URL + 'image',
                                                 headers=headers,
                                                 data=row,
                                                 files=image_data)

                        if response.status_code != 200:
                            print(response.text)
                            row['errorMessage'] = response.text
                            writer.writerow(row)
                            continue
                        else:
                            print(response.json()['ark_id'])
                            row["ARKID"] = response.json()['ark_id']
                            writer.writerow(row)
                except Exception as e:
                    print(e)
                    row['errorMessage'] = str(e)
                    writer.writerow(row)
                    continue

def main():
    parser = argparse.ArgumentParser(description="Upload images using provided batch info and image info files")
    parser.add_argument('image_info_path', type=str, help="Path to the image info CSV file")
    parser.add_argument('api_key', type=str, help="API key for authentication")

    args = parser.parse_args()

    image_info_path = args.image_info_path
    api_key = args.api_key

    batch_id = input("Enter an existing batch ID (or leave empty to create a new batch): ")
    #get batch info from input args
    if not batch_id:
        batch_info = {}
        print("Please provide the required and optional batch parameters:")
        param_institution = input("Enter parameter institution (optional): ")
        if param_institution:
            batch_info['institutionCode'] = param_institution

        param_batch_name = input("Enter parameter batch name (required): ")
        if param_batch_name:
            batch_info['batchName'] = param_batch_name

        param_pipeline = input("Enter parameter pipeline (optional):boundingbox/segmentation/landmark ")
        if param_pipeline:
            batch_info['pipeline'] = param_pipeline

        # param_creator = input("Enter parameter creator (optional): ")
        # if param_creator:
        #     batch_info['creator'] = param_creator

        param_comment = input("Enter parameter comment (optional): ")
        if param_comment:
            batch_info['creatorComment'] = param_comment

        param_codeRepository = input("Enter parameter codeRepo (optional): ")
        if param_codeRepository:
            batch_info['codeRepository'] = param_codeRepository

        param_url = input("Enter parameter url (optional): ")
        if param_url:
            batch_info['url'] = param_url

        param_citation = input("Enter parameter citation (optional): ")
        if param_citation:
            batch_info['bibliographicCitation'] = param_citation

        supplement_file_path = input('Enter path of supplement file(optional): ')

        batch_id = create_batch(batch_info, api_key, supplement_file_path, image_info_path)

    upload_images(batch_id, image_info_path, api_key)

if __name__ == '__main__':
    main()