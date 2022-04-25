"""
Script to bulk update Learn Course records with digital_product_url pointing directly to web course works pages. GOT IT?!@?!!?!?!?!?!?
"""


import csv
from learn.models.learn_course import LearnCourse


# -----------------------------------
# CONFIGURATION - ADJUST AS NECESSARY
# -----------------------------------

# which column in the CSV (0-based) has our Django master_ids
master_id_column_idx = 1

# which column in the CSV (0-based) has the WCW urls
wcw_url_column_idx = 0

# Filesystem location of the CSV
csv_file_path = '/tmp/wcw_urls.csv'

# Filesystem location of the CSV to write master_ids that are missing in Django
bad_ids_csv_path = '/tmp/lc_bad_master_ids.csv'

# Does the CSV have a header row? If True, the first line of the CSV will be skipped
skip_header = True


def main():
    bad_ids = []
    with open(csv_file_path) as csvfile:
        reader = csv.reader(csvfile)
        if skip_header:
            next(reader)
        for row in reader:
            lc = LearnCourse.objects.filter(
                master_id=row[master_id_column_idx].strip(),
                publish_status="DRAFT"
            ).first()
            if lc is not None:
                print('Found {} | {}, setting URL to {}'.format(
                    row[master_id_column_idx].strip(),
                    lc.title,
                    row[wcw_url_column_idx].strip()
                ))
                lc.event.digital_product_url = row[wcw_url_column_idx].strip()
                lc.event.save()
                lc.event.publish()
                lc.event.solr_publish()
            else:
                print('Learn Course with master ID {} not found in Django'.format(row[master_id_column_idx].strip()))
                bad_ids.append([row[master_id_column_idx].strip()])

    if bad_ids:
        # write out the bad_ids
        with open(bad_ids_csv_path, 'w') as outfile:
            writer = csv.writer(outfile)
            writer.writerow(['MASTER IDs MISSING IN DJANGO'])
            writer.writerows(bad_ids)
