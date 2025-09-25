from functions import run_python_file
from functions.get_files_info import get_files_info
from functions.get_file_content import get_file_content
from functions.write_file import write_file
from functions.run_python_file import run_python_file

def main():
    working_dir="calculator"
    
    #print(write_file(working_dir,"lorem.txt","Hello this is the new lorem ipsum"))
    print(run_python_file(working_dir,"main.py",["5 + 3"]))
main()

    