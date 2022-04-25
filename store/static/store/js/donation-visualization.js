"use strict";

function unique_array(a) {
	// returns array of strings without duplicates
	var _temp = {};
	var a_unique = [];
	for(var i = 0; i < a.length; i++) {
		var item = a[i];
		if(!_temp[item]) {
			_temp[item] = true;
			a_unique.push(item)
		}
	}
	return a_unique
}

function tweenText( oldValue, newValue, decimalPlaces ) {
	return function() {
		var $element = this;
  
 		var i = d3.interpolate( oldValue, newValue );
  
  		return function(t) {
    		$element.textContent = i(t).toLocaleString(undefined, {maximumFractionDigits: decimalPlaces, minimumFractionDigits: decimalPlaces});
  		};
	}
}

function DonationDataManager() {
	var self = this;

	this.count = 0;
	this.total = 0.00;
	this.queued_donors = [];
	this.donors = [];
	this.current_donor_index = 0; // when no queued donors, cycle through donors already displayed
	this.exclude_begintime = null; // used when querying for donors, to not get donors we already queried
	this.exclude_endtime = null; // used when querying for donors, to not get donors we already queried

	this.$count = d3.select("#donation-count .value");
	this.$amount = d3.select("#donation-amount .value");
	this.$donor = d3.select("#donation-donor .value");

	this.fetch_data = function(){
		return $.get("/foundation/donation/visualization/json/").then(function(response){
			if(response.success && response.data){

				console.log("SUCCESS!");

				var old_count = self.count;
				var old_total = self.total;

				self.count = response.data.donation_count;
				self.total = response.data.donation_amount;

				self.$count
					.transition()
					.duration(5000)
					.delay(0)
					.tween("span", tweenText(old_count, self.count, 0));

				self.$amount
					.transition()
					.duration(5000)
					.delay(0)
					.tween("span", tweenText(old_total, self.total, 2));

			}else{
				console.log("ERROR!");
			}
		});
	}

	this.fetch_donors = function(options) {
		options = options || {};
		return $.get("/foundation/donation/visualization/donors/json/", {"exclude_begintime":self.exclude_begintime, "exclude_endtime":self.exclude_endtime}).then(function(response){
			if(response.success && response.data){

				console.log("SUCCESS!");

				self.exclude_begintime = response.data.exclude_begintime;
				self.exclude_endtime = response.data.exclude_endtime;
				if(!options.block_queue) {
					Array.prototype.push.apply(self.queued_donors, unique_array(response.data.donors));
				}
				Array.prototype.push.apply(self.donors, response.data.donors);
				self.donors = unique_array(self.donors);

			}else{
				console.log("ERROR!");
			}
		});
	}

	// STILL WORKING ON THIS
	this.show_donor = function() {

		var donor_animation = self.$donor.transition()
			.duration(750)
			.style('opacity', 0)

		if(self.queued_donors.length){
			var donor = self.queued_donors.shift();
			donor_animation.transition()
					.text("Thank You "+ donor)
				.transition()
					.delay(500)
					.duration(750)
					.style('opacity', 1);
			// unshift donor off the front of the list, and show it
		} else if(self.donors.length) {
			// use current index to get, and show it
			var donor = self.donors[self.current_donor_index];
			donor_animation.transition()
					.text("Thank You "+ donor)
				.transition()
					.delay(500)
					.duration(750)
					.style('opacity', 1);

			self.current_donor_index++;
			if(self.current_donor_index >= self.donors.length){
				self.current_donor_index = 0
			}
		}
	}

	return this;
}

$(function(){

	var donation_manager = new DonationDataManager();

	donation_manager.fetch_data();

	// block queue fot initial fetch so we don't have to go through entire list before new donors appear
	donation_manager.fetch_donors({"block_queue":true});

	setInterval(function(){
		donation_manager.fetch_data();
		donation_manager.fetch_donors();
	}, 30000);

	setInterval(donation_manager.show_donor, 5000);

});















