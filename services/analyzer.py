def read_python_file(filepath):

    try:

        with open(filepath, "r", encoding="utf-8") as file:

            code = file.read()

        return True, code

    except Exception as e:

        return False, str(e)