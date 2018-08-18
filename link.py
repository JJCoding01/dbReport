import os
# from icecream import ic


def link(part_number, path='.'):
    """"search path for filename"""
    file_list = []
    for root, dirs, files in os.walk(path):
        for file in files:
            if file.startswith(str(part_number) + '_'):
                full_path = os.path.join(root, file)
                file_list.append(full_path)

    if file_list == []:
        return None
    else:
        file_list.sort()
        released = file_list[-1]
        return released


if __name__ == '__main__':
    pn = '1800257'
    path = 'D:\\Users\\Joey\\Documents\\Scripts\\Python\\MTI\\drawings\\PDF'
    latest = link(pn, path)
    print(latest)
