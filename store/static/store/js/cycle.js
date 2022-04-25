
var txt2giveSrc = 'https://fundraisers.txt2give.co/fundraisers/5c4b44853c5440000998f0af';
var apaDonorsSrc = '/foundation/donors/onsite/';

function switchIframe(src) {
    var iframe = document.getElementById('main');
    iframe.src = src;
}

var toggle = false;

function incrementPage(page) {
    if (page < numPages) {
        setTimeout(function() {
            incrementPage(page);
        }, 30000);
        toggle = !toggle;
        console.log(toggle);
        if (!toggle) {
            switchIframe(txt2giveSrc);
        } else {
            page = ++page;
            console.log(page);
            switchIframe(apaDonorsSrc + '?page=' + page)
        }
    } else {
        incrementPage(0)
    }
}

incrementPage(0);
