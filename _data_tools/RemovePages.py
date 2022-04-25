from pages.models import Page

def RemovePages(PageList, force=False):
    count = 0
    for url in PageList:
        qs = Page.objects.filter(url=url)       
        query_count = qs.count()
        to_delete = None 
        if query_count == 1:
            to_delete = qs.first()
        elif query_count == 3:
            qs.lone_page= None
            if qs[0].title == qs[1].title:
                to_delete = qs[2]
            elif qs[1].title == qs[2].title:
                to_delete = qs[0]
            elif qs[0].title == qs[2].title:
                to_delete = qs[1]
        if to_delete:        
            if force:  
                # to_delete.delete()
                print ("Delete")
                to_delete.delete()
                count += 1    
            else:
                rm = input("Would you like to delete "+ to_delete.title+ "?(Y/n)")
                if rm=='Y':
                    to_delete.delete()
                    count += 1
                else:        
                    print ("Did not Delete")
    return count
    