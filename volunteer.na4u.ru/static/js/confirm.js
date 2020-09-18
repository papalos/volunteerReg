"use strict"
function conf_del() {
    if (confirm("ВНИМАНИЕ! Ваши действия приведут к необратимым последствиям, запись будет невозможно восстановить. Вы действительно хотите удалить элемент?")) {
        return true;
    }
    else {
        return false;
    }
}

function conf_change() {
    if (confirm("ВНИМАНИЕ! Ваши действия приведут к необратимым последствиям. Все равно перейти к редактированию?")) {
        return true;
    }
    else {
        return false;
    }
}

function conf_cancel() {
    if (confirm("Ты уверен, что хочешь отказаться от участия в этом мероприятии? Помни, что оргкомитет рассчитывает на тебя и каждый раз, когда ты отменяешь участие, расстраивается один организатор")) {
        return true;
    }
    else {
        return false;
    }
}

function conf_reg() {
    if (confirm("Зарегистрировать пользователя?")) {
        return true;
    }
    else {
        return false;
    }
}

function conf_extrareg() {
    if (confirm("Вы уверены, что хотите совершить необратимое действие дорегистриции пользователя?")) {
        return true;
    }
    else {
        return false;
    }
}