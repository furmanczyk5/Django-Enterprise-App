// TODO: This is a little hacky...
var div525 = $('#5-25-learners-group-pricing');
var div26p = $('#26-learners-group-pricing');

// populate the <select> element with quantities
var selectDropdown = document.getElementById("quantity");

for (var i = 2; i < 101; i++) {
    var quantityOption = document.createElement("option");
    quantityOption.value = i;
    quantityOption.text = i;
    selectDropdown.add(quantityOption, null);
}

// register onchange handler for selectDropdown
selectDropdown.onchange = function() {

    var selectedQuantity = parseInt(this.value);
    var codePurchaseDiv = $('#codePurchase');

    if (selectedQuantity === 1) {
        codePurchaseDiv.show();
        div525.hide();
        div26p.hide();
    } else if (selectedQuantity >= 2 && selectedQuantity <= 4) {
        codePurchaseDiv.hide();
        div525.hide();
        div26p.hide();
    } else {
        codePurchaseDiv.hide();
        div525.show();
        div26p.show();
    }
    $('#product_option_id').val(setProductOption(this.value));
};

// determine the correct product option id from the quantity
function setProductOption(quantity) {
    // get all product options with their min and max quantities
    var optionMinMax = [];
    var allOptions = $('.product_options');
    $.each(allOptions, function() {
        var optionId = this.value;
        var nextElem = this.nextElementSibling;
        var minQuantity = parseInt(nextElem.value);
        var maxQuantity = parseInt(nextElem.nextElementSibling.value);
        optionMinMax.push([optionId, minQuantity, maxQuantity]);
    });

    var optionCode = null;
    var quantityInt = parseInt(quantity);

    optionMinMax.forEach(function(item) {
        if (quantityInt >= item[1] && quantityInt <= item[2]) {
            optionCode = item[0];
        }
    });
    return optionCode;
}

// hacky way of setting the correct redirect value if user chooses
// "Add to Cart and Return to APA Learn
document.getElementById("return_to_apa_learn").onmouseenter = function(e) {
    $('#redirect').val('https://learn.planning.org/catalog/')
};

document.getElementById("return_to_apa_learn").onmouseleave = function(e) {
    $('#redirect').val('store:cart')
};


