#!/usr/bin/env python
#-*-coding:utf-8-*-

from web import form



vauthor = form.regexp(r".+", "Name can not be empty!")
vemail = form.regexp(r".*@.*", "Email address is empty or not valid!")
vcomment = form.regexp(r".+", "Comment can not be empty!")

comment_form = form.Form(
    form.Textbox("author", vauthor, size="22", tabindex="1", value="", class_="comment"),
    form.Textbox("email", vemail, size="22", tabindex="2", value="", class_="comment"),
    form.Textbox("url", size="22", tabindex="3", value="", class_="comment"),
    form.Textarea("comment", vcomment, cols="100%", rows="10", tabindex="4"),
    form.Button("submit", type="submit", class_="submit", tabindex="5",
                html="Submit Comment", title="Please review your comment before you submit"),
)

settings_form = form.Form(
    form.Textbox("title", maxlength="200", value=""),
    form.Textbox("subtitle", maxlength="200", value=""),
    form.Textarea("notice", rows="2", cols="10"),
    form.Textbox("keywords", maxlength="200", value=""),
    form.Textbox("description", maxlength="200", value=""),
    form.Textbox("email", vemail, maxlength="200", value=""),
    form.Textbox("domain", maxlength="200", class_="regular-text", value=""),
    form.Button("submit", type="submit", class_="button-primary", html="Save changes"),
)












    
