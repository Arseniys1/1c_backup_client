

def check_content_types(files, content_types):
    wrong_files = []
    passed_files = []
    for file in files:
        passed = False
        for content_type in content_types:
            if file.content_type == content_type:
                passed_files.append(file)
                passed = True
                break
        if not passed:
            wrong_files.append(file)
    return passed_files, wrong_files


