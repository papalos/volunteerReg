"use strict"
// шаблон для проверки почты
let regmail = /^([a-z0-9_-]+\.)*[a-z0-9_-]+@[a-z0-9_-]+(\.[a-z0-9_-]+)*\.[a-z]{2,6}$/;
// шаблон для проверки телефона
let regtel = /^(\+)?[0-9]{1,3}(\s)?(\()?[0-9]{3}(\))?[\d\-\s]{7,17}$/; //

function gId(id) {
    return document.getElementById(id);
}

// поле почты и его лейбл сообщения об ошибке
let email = gId("vltremail");
let errmail = gId("erremail");
let err2mail = gId("err2email");

// поле телефона и его лейбл сообщения об ошибке
let tel = gId("vltrtel");
let errtel = gId("errtel");

// поля логин и пароль и их лейбл сообщения об ошибке
let log = gId("vlrtlog");
let pass = gId("vltrpass");
let errpass = gId("errpass");

// чекбокс для продтверждения подлиности данных
let ch = gId("check");

// чекбокс для продтверждения подлиности данных
let b = gId("butt");



// переменные для флагов
let f1 = false, f2 = false, f3 = false, f4 = false;
b.setAttribute('disabled', 'disabled');
console.log("test");


// объект AJAX
let ajax = new XMLHttpRequest();

ajax.onreadystatechange = function () {
    if (ajax.readyState != 4) return;

    if (ajax.status != 200) {
        alert(ajax.status + ': ' + ajax.statusText); // удалить в конечной версии
    } else {
        //alert(ajax.responseText);
        if (ajax.responseText == "True") {
            err2mail.style.display = 'inline';
            f1 = false;
        }
        else {
            err2mail.style.display = 'none';
            f1 = true;
        }
        control();
    }
}



email.onblur = function () {
    let flag = regmail.test(email.value);
    if (flag) {
        errmail.style.display = "none";
        ajax.open('get', '/xxx?mail=' + email.value, true);
        ajax.send();
    }
    else {
        errmail.style.display = "inline";
        err2mail.style.display = 'none';
    }
    //console.log(flag);
}

tel.onblur = function () {
    let f = regtel.test(tel.value);
    if (f) {
        errtel.style.display = "none";
        f2 = true;
    }
    else {
        errtel.style.display = "inline";
        f2 = false;
    }
    control();
}

pass.onblur = function () {
    let ecv = (log.value !== pass.value);
    if (ecv) {
        errpass.style.display = "none";
        f3 = true;
    }
    else {
        errpass.style.display = "block";
        f3 = false;
    }
    control();
}


ch.onchange = function () {
    if (ch.checked) {
        f4 = true;
    }
    else {
        f4 = false;
    }
    control();
};

function control() {
    if (f1 && f2 && f3 && f4) {
        b.removeAttribute('disabled');
    }
    else {
        b.setAttribute('disabled', 'disabled');
    }
    // console.log(f1 + f2 + f3 + f4); //test
}