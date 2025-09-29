import os

def write_list_to_file(string_list: list):
    """
    Writes each string from a list to a new line in a text file.

    Args:
        filename (str): The name of the file to write to.
        string_list (list[str]): The list of strings to write.
    """
    # Using a 'with' statement ensures the file is automatically closed,
    # even if an error occurs. The 'w' mode opens the file for writing,
    # and will create the file if it does not exist, or overwrite it if it does.
    filename = r"/home/jonas/coding/xArm/myLibs/history_saver/saves/out_put_1.txt"
    try:
        with open(filename, 'w') as file:
            for item in string_list:
                if isinstance(item,str):
                    # Write the item to the file, followed by a newline character '\n'
                    file.write(item + '\n')
        print(f"Successfully wrote the list to '{filename}'.")
    except IOError as e:
        print(f"An error occurred while writing to the file: {e}")