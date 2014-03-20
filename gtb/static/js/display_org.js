$(document).on("ready", function() {
    var org_id = window.location.pathname.split("/")[2];
    console.log(org_id)

    $("#members").on("click", "button", function() {
        var conf = confirm("Are you sure you want to remove that user?");
        if (conf) {
            var data = new Object();
            data['user_id'] = $(this).val(); 

            // $(this) is something else when a new function is entered.
            // It was not correct so we made a copy of the row to remove
            // here.
            var row = $(this).parent().parent()

            $.post('/organization/' + org_id + '/users/remove', data).done(function(resp) {
                if (resp['message'] == 'Success!') {
                    row.remove(); 
                }
            });
        }
    });
});
