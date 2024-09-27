import os
cwd=os.getcwd()
os.chdir(os.path.dirname(cwd))
print(cwd)

def get_lines(folder_path):
    files=os.listdir(folder_path)
    count=0
    for file in files:
        if os.path.isfile(folder_path+'/'+file):
            if '__pycache__' not in folder_path+'/'+file:
                with open(folder_path + '/' + file, encoding='utf-8') as f:
                    for line in f:
                        count += 1
        elif os.path.isdir(folder_path+'/'+file):
            count+=get_lines(folder_path+'/'+file)

    return count

lines=get_lines(cwd+'/core')
print(lines)
