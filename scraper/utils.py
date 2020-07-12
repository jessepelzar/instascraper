def create_text_file(entry_now):
    f = open("entry.txt", "w+")
    f.write(entry_now)
    f.close()
