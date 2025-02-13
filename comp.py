import os

def compile_po_file(po_file_path, output_dir):
    mo_file_name = os.path.splitext(os.path.basename(po_file_path))[0] + '.mo'
    mo_file_path = os.path.join(output_dir, mo_file_name)
    command = f'msgfmt "{po_file_path}" -o "{mo_file_path}"'
    os.system(command)

if __name__ == "__main__":

    compile_po_file('locales\pt-BR\LC_MESSAGES\main.po', 'locales\pt-BR\LC_MESSAGES')
