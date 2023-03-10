def create_element(soup, tag_name, tag_text_content=None, tag_inner=None, classname=None, id=None):
    new_element = soup.new_tag(tag_name)
    if tag_text_content:
        new_element.string = tag_text_content
    if tag_inner:
        if isinstance(tag_inner, list):
            for element in tag_inner:
                new_element.append(element)
        else:
            new_element.append(tag_inner)
    if classname:
        new_element["class"] = classname
    if id:
        new_element["id"] = id
    return new_element


def get_soup_from(tag):  # once the parents iterator runs out the last element will be the initial soup
    for soup in tag.parents:
        continue
    return soup


def prepare_target_anchor(target_anchor):
    target_anchor["class"] = "target"
    target_anchor["target"] = "_blank"
    del target_anchor["title"]
    return target_anchor


def highlight_target_anchor(soup, target_anchor):
    for tag in soup.find_all(True):
        if tag == target_anchor:
            prepare_target_anchor(tag)
    return soup


def remove_all_tags(soup, tag_name, action, save=None, save_action=None):
    tags = soup.find_all(tag_name)
    if not tags:
        return soup
    for tag in tags:
        if tag == save:
            save_action(tag)
            continue
        if action == "delete":
            tag.decompose()
        elif action == "unwrap":
            tag.unwrap()
    return soup


def element_has_parent_with_tagname(element, tag_name):
    for parent in element.parents:
        if parent.name == tag_name:
            return parent
    return False


def derive_new_table(target_anchor, table):
    soup = get_soup_from(target_anchor)  # todo: REFACTOR!
    table_rows = table.select("tbody tr", recursive=False)
    table_title = table_rows.pop(0)
    remove_all_tags(table_title, "abbr", "delete")
    new_table_header = create_element(soup, "h2", tag_text_content=table_title.get_text())
    new_table_element = create_element(soup, "table")
    for row in table_rows:
        new_table_row = create_element(soup, "tr")
        if row.find("th", recursive=False):
            current_row_title = row.find("th").get_text()
            new_row_title = create_element(soup, "th", tag_text_content=current_row_title)
            new_table_row.append(new_row_title)
        row_data_list = row.find("ul")
        new_row_data = create_element(soup, "td")
        row_data_list = remove_all_tags(row_data_list, "a", "unwrap", save=target_anchor, save_action=prepare_target_anchor)
        items = row_data_list.select("li")
        new_list = create_element(soup, "ul", tag_inner=items)
        new_row_data.append(new_list)
        new_table_row.append(new_row_data)
        new_table_element.append(new_table_row)
    return create_element(soup, "div", tag_inner=[new_table_header, new_table_element])


def derive_new_table_sidebar(target_anchor, table):  # todo: REFACTOR!
    soup = get_soup_from(target_anchor)
    new_table_element = create_element(soup, "table")
    table_rows = table.select("tbody tr", recursive=False)
    new_table_header = create_element(soup, "th")
    if table_rows[0].find("td", {"class": "sidebar-pretitle"}):  # table has a pretitle
        table_pre_title_text = table_rows.pop(0).get_text()
        pre_title = create_element(soup, "h3", tag_text_content=table_pre_title_text)
        new_table_header.append(pre_title)
    table_row = table_rows.pop(0)
    table_title = table_row.get_text()
    new_table_title = create_element(soup, "h2", tag_text_content=table_title)
    new_table_header.append(new_table_title)
    for row in table_rows:
        if row.find("td", {"class": "sidebar-content"}):
            new_table_row = create_element(soup, "tr")
            row_title_text = row.find("div", {"class": "sidebar-list-title"}).get_text()
            new_row_title = create_element(soup, "th", tag_text_content=row_title_text)
            new_table_row.append(new_row_title)
            inner_list = row.find("div", {"class": "sidebar-list-content"}).find("ul")
            new_row_data = create_element(soup, "td")
            inner_list = remove_all_tags(inner_list, "a", action="unwrap", save=target_anchor, save_action=prepare_target_anchor)
            items = inner_list.find_all("li")
            new_list = create_element(soup, "ul", tag_inner=items)
            new_row_data.append(new_list)
            new_table_row.append(new_row_data)
            new_table_element.append(new_table_row)
    return create_element(soup, "div", tag_inner=[new_table_header, new_table_element])


def derive_new_table_infobox(target_anchor, table):
    if "biota" in table.get("class"):
        return derive_new_biota_infobox(target_anchor, table)
    return derive_new_table_infobox_vcard(target_anchor, table)


def derive_new_table_infobox_vcard(target_anchor, table):  # todo: REFACTOR!
    soup = get_soup_from(target_anchor)
    table_rows = table.select("tbody tr", recursive=False)
    new_table_element = create_element(soup, "table")
    new_thumbnail = None
    for row in table_rows:
        if row.find("td", {"class": "infobox-image"}):
            thumbnail = row.find("img")
            description = row.find("div", {"class": "infobox-caption"}).get_text()
            description = create_element(soup, "p", tag_text_content=description)
            new_thumbnail = create_element(soup, "div", tag_inner=[thumbnail, description], classname="thumbnail-desc")
            continue
        if row.find("th", {"class": "infobox-label"}):
            new_table_row = create_element(soup, "tr")
            row_title_text = row.find("th", {"class": "infobox-label"}).get_text()
            new_row_title = create_element(soup, "th", tag_text_content=row_title_text)
            new_table_row.append(new_row_title)
            row_data = row.find("td", {"class": "infobox-data"})
            inner_list = row_data.find("ul")
            if inner_list:
                new_row_data = create_element(soup, "td")
                inner_list = remove_all_tags(inner_list, "a", action="unwrap", save=target_anchor, save_action=prepare_target_anchor)
                items = inner_list.find_all("li")
                new_list = create_element(soup, "ul", tag_inner=items)
                new_row_data.append(new_list)
                new_table_row.append(new_row_data)
                new_table_element.append(new_table_row)
                continue
            row_data_fragments = list()
            for element in row_data:
                if element == target_anchor:
                    target_anchor = prepare_target_anchor(element)
                    row_data_fragments.append(target_anchor)
                    continue
                text_fragment = f" {element.get_text().strip()} "
                row_data_fragments.append(text_fragment)
            new_row_data = create_element(soup, "td", tag_inner=row_data_fragments)
            new_table_row.append(new_row_data)
            new_table_element.append(new_table_row)
    return create_element(soup, "div", tag_inner=[new_thumbnail, new_table_element])


def derive_new_biota_infobox(target_anchor, table):
    soup = get_soup_from(target_anchor)
    table_rows = table.select("tbody tr", recursive=False)
    new_table_element = create_element(soup, "table")
    for row in table_rows:
        row_data = row.select("td")
        if row_data and len(row_data) >= 2:
            remove_all_tags(row, "a", action="unwrap", save=target_anchor, save_action=prepare_target_anchor)
            new_row_header = create_element(soup, "th", tag_text_content=row_data[0].get_text().replace(":", "").strip())
            new_row = create_element(soup, "tr", tag_inner=[new_row_header, row_data[1]])
            new_table_element.append(new_row)
    return create_element(soup, "div", tag_inner=new_table_element)


def derive_new_thumbnail(target_anchor, thumbnail_container):
    soup = get_soup_from(target_anchor)
    image_tag = thumbnail_container.img.extract()
    caption = thumbnail_container.find("div", {"class": "thumbcaption"})
    caption.find("div", {"class": "magnify"}).decompose()
    caption = remove_all_tags(caption, "a", action="unwrap", save=target_anchor, save_action=prepare_target_anchor)
    return create_element(soup, "div", tag_inner=[image_tag, caption])
