# django-htmlpurifier
A silly but useful hack for sanitizing untrusted HTML input in Django forms via PHP's [HTML Purifier](http://htmlpurifier.org/)

## Prerequisites
PHP 5.0.5+ w/ CLI  
[HTML Purifier](http://htmlpurifier.org/) library - standard, lite, or PEAR distribution  
_NOTE: `HTMLPurifier.auto.php` should be in your PHP path._   
A willingness to mix Python/Django with PHP


## Installation
Add 'htmlpurifier' to `INSTALLED_APPS` in your project's settings.py.

## Configuration
django-htmlpurifier is ready to use out-of-the-box, assuming that you are happy with
the PHP HTML Purifier's [default settings](http://htmlpurifier.org/download#Installation).

Otherwise, django-htmlpurifier currently supports the following settings, definable in settings.py:  
`HTMLPURIFIER_SCRIPT_PATH`: An absolute path to a custom PHP processing script (see below)

## Usage
Using django-htmlpurifier is very simple.

Import the htmlpurifier module:  
`import htmlpurifier`

Define a field that should be sanitized:  
`MyHtmlField = htmlpurifier.HTMLField()`  
or perhaps  
`MyHtmlField = htmlpurifier.HTMLField(widget=forms.TextArea)`  

*HTMLField() is a subclass of Django's CharField.*

If for some reason you don't want to deal with forms and just need a low-level function that HTML-purifies a string input, do:   
`htmlpurifier.purify(my_html_str)` 


## Writing your own PHP processing script
django-htmlpurifier ships with a very basic PHP script that provides an interface to
the PHP HTML Purifier library using its default settings. If the default settings 
do not float your boat, please refer to the [HTML Purifier configuration reference](http://htmlpurifier.org/live/configdoc/plain.html).
