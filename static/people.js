var r_is_student = document.getElementById("is_student");
var r_is_general = document.getElementById("is_general");

var form = document.getElementById("people_form");
var student_items = form.getElementsByClassName("student");

r_is_student.onchange = enable_student;
r_is_general.onchange = enable_general;

if (r_is_student.checked) {
	enable_student();
} else if (r_is_general.checked) {
	enable_general();
}

function enable_student() {
	for (i in student_items) {
		var row = student_items[i];
		try { row.classList.remove('hide'); } catch(err) {}
	}
}

function enable_general() {
	for (i in student_items) {
		var row = student_items[i];
		try { row.classList.add('hide'); } catch(err) {}
	}
}
