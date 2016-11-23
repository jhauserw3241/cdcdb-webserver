// ----------------------------------------------------------------------------
// events/new.html

var r_is_meeting = document.getElementById("is_meeting");
var r_is_competition = document.getElementById("is_competition");
var r_is_general = document.getElementById("is_general");

var form = document.getElementById("event_form");
if (form) {
    var meeting_items = form.getElementsByClassName("meeting");
    var competition_items = form.getElementsByClassName("competition");

    r_is_meeting.onchange = enable_meeting;
    r_is_competition.onchange = enable_competition;
    r_is_general.onchange = enable_general;

    if (r_is_meeting.checked) {
        enable_meeting();
    } else if (r_is_competition.checked) {
        enable_competition();
    } else if (r_is_general.checked) {
        enable_general();
    }
}

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

function enable_general() {
	for (i in meeting_items) {
		var row = meeting_items[i];
		try { row.classList.add('hide'); } catch(err) {}
	}
	for (i in competition_items) {
		var row = competition_items[i];
		try { row.classList.add('hide'); } catch(err) {}
	}
}

// ----------------------------------------------------------------------------
// events/index.html

var cb_show_past_events = document.getElementById("show_past_events");
var past_events = document.getElementsByClassName("past_event");

cb_show_past_events.onchange = toggle_past_events;

function toggle_past_events() {
    for (i in past_events) {
        var e = past_events[i];
        console.log(e);
        try {
            if (cb_show_past_events.checked)
                e.classList.remove('hide');
            else
                e.classList.add('hide');
        } catch(err) {}
    }
}
