/*global ace, define, exports*/
var language = {};
language.setlangmode = function language_setlangmode(input) {
    "use strict";
    var langmap = {
        coldfusion: "markup",
        css       : "css",
        csv       : "csv",
        dustjs    : "html",
        ejs       : "html",
        handlebars: "html",
        html      : "html",
        html_ruby : "html",
        javascript: "javascript",
        json      : "javascript",
        jsp       : "markup",
        jsx       : "javascript",
        less      : "css",
        markup    : "markup",
        php       : "html",
        qml       : "qml",
        scss      : "css",
        swig      : "html",
        text      : "text",
        titanium  : "tss",
        tss       : "tss",
        twig      : "html",
        velocity  : "velocity",
        xhtml     : "markup",
        xml       : "markup"
    };
    if (typeof input !== "string") {
        return "javascript";
    }
    if (input.indexOf("html") > -1) {
        return "html";
    }
    if (langmap[input] === undefined) {
        return "javascript";
    }
    return langmap[input];
};
language.nameproper  = function language_nameproper(input) {
    "use strict";
    var langmap = {
        coldfusion: "ColdFusion",
        dustjs    : "Dust.js",
        ejs       : "EJS Template",
        elm       : "Elm Template",
        handlebars: "Handlebars Template",
        html_ruby : "ERB (Ruby) Template",
        java      : "Java (not supported yet)",
        javascript: "JavaScript",
        jsp       : "JSTL (JSP)",
        jsx       : "React JSX",
        liquid    : "Liquid Template",
        markup    : "markup",
        scss      : "SCSS",
        text      : "Plain Text",
        titanium  : "Titanium Stylesheets",
        tss       : "Titanium Stylesheets",
        twig      : "HTML TWIG Template",
        typescript: "TypeScript (not supported yet)",
        velocity  : "Apache Velocity",
        volt      : "Volt Template"
    };
    if (typeof input !== "string" || langmap[input] === undefined) {
        return input.toUpperCase();
    }
    return langmap[input];
};
// [0] = language value for ace mode [1] = prettydiff language category from [0]
// [2] = pretty formatting for text output to user
language.auto = function language_auto(sample, defaultLang) {
    "use strict";
    var b         = [],
        c         = 0,
        output    = function language_auto_output(langname) {
            if (langname === "unknown") {
                return [
                    defaultLang, language.setlangmode(defaultLang),
                    "unknown"
                ];
            }
            if (langname === "xhtml" || langname === "markup") {
                return ["xml", "html", "XHTML"];
            }
            if (langname === "tss") {
                return ["tss", "tss", "Titanium Stylesheets"];
            }
            return [
                langname, language.setlangmode(langname),
                language.nameproper(langname)
            ];
        },
        cssA      = function language_auto_cssA() {
            if ((/\$[a-zA-Z]/).test(sample) === true || (/\{\s*(\w|\.|\$|#)+\s*\{/).test(sample) === true) {
                return output("scss");
            }
            if ((/@[a-zA-Z]/).test(sample) === true || (/\{\s*(\w|\.|@|#)+\s*\{/).test(sample) === true) {
                return output("less");
            }
            return output("css");
        },
        notmarkup = function language_auto_notmarkup() {
            var d               = 0,
                join            = "",
                flaga           = false,
                flagb           = false,
                javascriptA     = function language_auto_notmarkup_javascriptA() {
                    if (sample.indexOf("(") > -1 || sample.indexOf("=") > -1 || (sample.indexOf(";") > -1 && sample.indexOf("{") > -1)) {
                        if ((/:\s*((number)|(string))/).test(sample) === true && (/((public)|(private))\s+/).test(sample) === true) {
                            return output("typescript");
                        }
                        return output("javascript");
                    }
                    return output("unknown");
                },
                cssOrJavaScript = function language_auto_notmarkup_cssOrJavaScript() {
                    if ((/:\s*((number)|(string))/).test(sample) === true && (/((public)|(private))\s+/).test(sample) === true) {
                        return output("typescript");
                    }
                    if ((/((public)|(private))\s+(((static)?\s+(v|V)oid)|(class)|(final))/).test(sample) === true) {
                        return output("java");
                    }
                    if ((/\sclass\s+\w/).test(sample) === false && (/<[a-zA-Z]/).test(sample) === true && (/<\/[a-zA-Z]/).test(sample) === true && ((/\s?\{%/).test(sample) === true || (/\{(\{|#)(?!(\{|#|\=))/).test(sample) === true)) {
                        return output("twig");
                    }
                    if ((/^\s*(\$|@)/).test(sample) === false && ((/:\s*(\{|\(|\[)/).test(sample) === true || (/(\{|\s|;)render\s*\(\)\s*\{/).test(sample) === true || (/^(\s*return;?\s*\{)/).test(sample) === true) && (/(\};?\s*)$/).test(sample) === true) {
                        return output("javascript");
                    }
                    if ((/\{\{#/).test(sample) === true && (/\{\{\//).test(sample) === true && (/<\w/).test(sample) === true) {
                        return output("handlebars");
                    }
                    if ((/\{\s*(\w|\.|@|#)+\s*\{/).test(sample) === true) {
                        return output("less");
                    }
                    if ((/\$(\w|-)/).test(sample) === true) {
                        return output("scss");
                    }
                    if ((/(;|\{|:)\s*@\w/).test(sample) === true) {
                        return output("less");
                    }
                    return output("css");
                };
            for (d = 1; d < c; d += 1) {
                if (flaga === false) {
                    if (b[d] === "*" && b[d - 1] === "/") {
                        b[d - 1] = "";
                        flaga    = true;
                    } else if (flagb === false && b[d] === "f" && d < c - 6 && b[d + 1] === "i" && b[d + 2] === "l" && b[d + 3] === "t" && b[d + 4] === "e" && b[d + 5] === "r" && b[d + 6] === ":") {
                        flagb = true;
                    }
                } else if (flaga === true && b[d] === "*" && d !== c - 1 && b[d + 1] === "/") {
                    flaga    = false;
                    b[d]     = "";
                    b[d + 1] = "";
                } else if (flagb === true && b[d] === ";") {
                    flagb = false;
                    b[d]  = "";
                }
                if (flaga === true || flagb === true) {
                    b[d] = "";
                }
            }
            join = b.join("");
            if ((/^(\s*(\{|\[)(?!%))/).test(sample) === true && (/((\]|\})\s*)$/).test(sample) && sample.indexOf(",") !== -1) {
                return output("json");
            }
            if ((/((\}?(\(\))?\)*;?\s*)|([a-z0-9]("|')?\)*);?(\s*\})*)$/i).test(sample) === true && ((/(((var)|(let)|(const)|(function)|(import))\s+(\w|\$)+[a-zA-Z0-9]*)/).test(sample) === true || (/console\.log\(/).test(sample) === true || (/export\s+default\s+class\s+/).test(sample) === true || (/document\.get/).test(sample) === true || (/((\=|(\$\())\s*function)|(\s*function\s+(\w*\s+)?\()/).test(sample) === true || sample.indexOf("{") === -1 || (/^(\s*if\s+\()/).test(sample) === true)) {
                return javascriptA();
            }
            if (sample.indexOf("{") !== -1 && (/^(\s*[\{\$\.#@a-z0-9])|^(\s*\/(\*|\/))|^(\s*\*\s*\{)/i).test(sample) === true && (/^(\s*if\s*\()/).test(sample) === false && (/\=\s*(\{|\[|\()/).test(join) === false && (((/(\+|-|\=|\?)\=/).test(join) === false || (/\/\/\s*\=+/).test(join) === true) || ((/\=+('|")?\)/).test(sample) === true && (/;\s*base64/).test(sample) === true)) && (/function(\s+\w+)*\s*\(/).test(join) === false) {
                return cssOrJavaScript();
            }
            if ((/"\s*:\s*\{/).test(sample) === true) {
                return output("tss");
            }
            if (sample.indexOf("{\%") > -1) {
                return output("twig");
            }
            return output("unknown");
        },
        markup    = function language_auto_markup() {
            var html = function language_auto_markup_html() {
                if ((/<%\s*\}/).test(sample) === true) {
                    return output("ejs");
                }
                if ((/<%\s*end/).test(sample) === true) {
                    return output("html_ruby");
                }
                if ((/\{\{(#|\/|\{)/).test(sample) === true) {
                    return output("handlebars");
                }
                if ((/\{\{end\}\}/).test(sample) === true) {
                    //place holder for Go lang templates

                    return output("html");
                }
                if ((/\s?\{%/).test(sample) === true && (/\{(\{|#)(?!(\{|#|\=))/).test(sample) === true) {
                    return output("twig");
                }
                if ((/<\?/).test(sample) === true) {
                    return output("php");
                }
                if ((/<jsp:include\s/).test(sample) === true || (/<c:((set)|(if))\s/).test(sample) === true) {
                    return output("jsp");
                }
                if ((/\{(#|\?|\^|@|<|\+|~)/).test(sample) === true && (/\{\//).test(sample) === true) {
                    return output("dustjs");
                }
                return output("html");
            };
            if ((/^(\s*<!doctype\ html>)/i).test(sample) === true || (/^(\s*<html)/i).test(sample) === true || ((/^(\s*<!DOCTYPE\s+((html)|(HTML))\s+PUBLIC\s+)/).test(sample) === true && (/XHTML\s+1\.1/).test(sample) === false && (/XHTML\s+1\.0\s+(S|s)((trict)|(TRICT))/).test(sample) === false)) {
                return html();
            }
            if ((/<jsp:include\s/).test(sample) === true || (/<c:((set)|(if))\s/).test(sample) === true) {
                return output("jsp");
            }
            if ((/<%\s*\}/).test(sample) === true) {
                return output("ejs");
            }
            if ((/<%\s*end/).test(sample) === true) {
                return output("html_ruby");
            }
            if ((/\{\{(#|\/|\{)/).test(sample) === true) {
                return output("handlebars");
            }
            if ((/\{\{end\}\}/).test(sample) === true) {
                //place holder for Go lang templates

                return output("xml");
            }
            if ((/\s?\{%/).test(sample) === true && (/\{\{(?!(\{|#|\=))/).test(sample) === true) {
                return output("twig");
            }
            if ((/<\?(?!(xml))/).test(sample) === true) {
                return output("php");
            }
            if ((/\{(#|\?|\^|@|<|\+|~)/).test(sample) === true && (/\{\//).test(sample) === true) {
                return output("dustjs");
            }
            if ((/<jsp:include\s/).test(sample) === true || (/<c:((set)|(if))\s/).test(sample) === true) {
                return output("jsp");
            }
            return output("xml");
        };
    if (sample === null) {
        return;
    }
    if ((/\sclass\s+\w/).test(sample) === false && (/(\s|;|\})((if)|(for)|(function\s*\w*))\s*\(/).test(sample) === false && (/((var)|(let)|(const))\s*\w/).test(sample) === false && (/return\s*\w*\s*(;|\})/).test(sample) === false && (sample === undefined || (/^(\s*#(?!(!\/)))/).test(sample) === true || (/\n\s*(\.|@)\w+(\(?|(\s*:))/).test(sample) === true)) {
        return cssA();
    }
    b = sample
        .replace(/\[[a-zA-Z][\w\-]*\=("|')?[a-zA-Z][\w\-]*("|')?\]/g, "")
        .split("");
    c = b.length;
    if ((/^(\s*\{(%|#|\{))/).test(sample) === true) {
        return markup();
    }
    if ((/^([\s\w\-]*<)/).test(sample) === false && (/(>[\s\w\-]*)$/).test(sample) === false) {
        return notmarkup();
    }
    if ((((/(>[\w\s:]*)?<(\/|!)?[\w\s:\-\[]+/).test(sample) === true || (/^(\s*<\?xml)/).test(sample) === true) && ((/^([\s\w]*<)/).test(sample) === true || (/(>[\s\w]*)$/).test(sample) === true)) || ((/^(\s*<s((cript)|(tyle)))/i).test(sample) === true && (/(<\/s((cript)|(tyle))>\s*)$/i).test(sample) === true)) {
        return markup();
    }
    return output("unknown");
};
if (typeof exports === "object" || typeof exports === "function") {
    //commonjs and nodejs support
    exports.api = language;
} else if ((typeof define === "object" || typeof define === "function") && (ace === undefined || ace.prettydiffid === undefined)) {
    //requirejs support
    define(function requirejs(require, exports) {
        "use strict";
        exports.api = language;
        //worthless if block to appease RequireJS and JSLint
        if (typeof require === "number") {
            return require;
        }
        return exports.api;
    });
}
