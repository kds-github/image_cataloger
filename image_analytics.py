from tkinter import messagebox
import pandas as pd
import os
from datetime import datetime

def get_image_statistics(directory_path):
    # create an empty DataFrame to store the statistics
    statistics_df = pd.DataFrame(columns=['Directory_Path', 'Processed_Date', 'Image_Year', 'Type', 'Count', 'Size (MB)'])
    
    # get the current date and time
    processed_date = datetime.now().strftime('%m/%d/%Y %H:%M')
    
    # loop through the directory and its subdirectories
    for root, dirs, files in os.walk(directory_path):
        for file in files:
            # get the file extension and check if it's an image file
            ext = os.path.splitext(file)[-1].lower()
            if ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp']:
                # get the file creation year and type
                file_path = os.path.join(root, file)
                create_time = os.path.getctime(file_path)
                create_year = datetime.fromtimestamp(create_time).strftime('%Y')
                file_type = ext.upper()
                
                # get the file size in MB
                size_mb = os.path.getsize(file_path) / (1024 * 1024)
                
                # add the file data to the DataFrame
                row = {
                    'Directory_Path': directory_path,
                    'Processed_Date': processed_date,
                    'Image_Year': create_year,
                    'Type': file_type,
                    'Count': 1,
                    'Size (MB)': size_mb
                }
                statistics_df = pd.concat([statistics_df, pd.DataFrame(row, index=[0])], ignore_index=True)
    
    # group the DataFrame by year and type and get the count and sum of file sizes
    grouped_df = statistics_df.groupby(['Image_Year', 'Type']).agg({'Count': 'sum', 'Size (MB)': 'sum'}).reset_index()
    
    # sort the DataFrame by size_mb
    grouped_df['Size (MB)'] = pd.to_numeric(grouped_df['Size (MB)']) # convert the size column to numeric
    sorted_df = grouped_df.sort_values(['Size (MB)'], ascending=[False])
    
    # add the directory path and processed date to the DataFrame
    sorted_df['Directory_Path'] = directory_path
    sorted_df['Processed_Date'] = processed_date
    
    # reorder the columns
    sorted_df = sorted_df[['Directory_Path', 'Processed_Date', 'Image_Year', 'Type', 'Count', 'Size (MB)']]
    
    # round the Size (MB) column to two decimal places
    sorted_df['Size (MB)'] = sorted_df['Size (MB)'].round(2)
    
    # write the results to a tab delimited file
    sorted_df.to_csv(output_file_path, sep='\t', index=False)
    
    return sorted_df

def write_results_to_file(directory_path, output_file_path):
    # get the image statistics for the directory
    image_statistics = get_image_statistics(directory_path)

    # write the statistics to a tab delimited file
    image_statistics.to_csv(output_file_path, sep='\t', index=False)

    print(f'Successfully saved image statistics to {output_file_path}')
    messagebox.showinfo("Image Analytics", f"Done")

if __name__ == '__main__':
    # Set the directory to search, the output filename, and the processed date
    default_search_path = os.path.expanduser("~")
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_file_path = os.path.join(script_dir, "file_analysis.txt")   
    print("Analyzing image files..")
    write_results_to_file(default_search_path, output_file_path)
