
def association_list_search(element_search, association_list):
    for data_tuple in association_list:
        if element_search == data_tuple[0]:
            return data_tuple
    return None


