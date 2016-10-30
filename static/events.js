var r_is_meeting = document.getElementById("is_meeting");
var r_is_competition = document.getElementById("is_competition");

var form = document.getElementById("event_form");
var meeting_items = form.getElementsByClassName("meeting");
var competition_items = form.getElementsByClassName("competition");

r_is_meeting.onchange = enable_meeting;
r_is_competition.onchange = enable_competition;

function enable_meeting() {
	for (i in meeting_items) {
		var row = meeting_items[i];
		try { row.classList.remove('hide'); } catch(err) {}
	}
	for (i in competition_items) {
		var row = competition_items[i];
		try { row.classList.add('hide'); } catch(err) {}
	}
}

function enable_competition() {
	for (i in meeting_items) {
		var row = meeting_items[i];
		try { row.classList.add('hide'); } catch(err) {}
	}
	for (i in competition_items) {
		var row = competition_items[i];
		try { row.classList.remove('hide'); } catch(err) {}
	}
}
