

$(document).ready(function() {
    $("#events_datatable").DataTable(
        {
            columnDefs: [
                {width: "40px", targets: -1},  // CM
            ],
            order: [[ 3, "desc"]],  // begin time
        }

    );

});
