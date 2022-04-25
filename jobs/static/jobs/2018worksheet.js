//
//  2018worksheet.js   APA/AICP 2018 Salary Worksheet   #18840    05/21/2018
//
    var emp      = -1;
    var ed       = -1;
  	var aicp     = -1;
  	var exp      = -1;
  	var sup      = -1;
  	var dir      = -1;
  	var sal = 0;
  	
//  ------------------------------------------------------------
function calc()
{
  var sal = 0, x = 0;
  var ok = getvars();
  if (ok)
  {
    emp = parseFloat(emp);
    switch (emp)
      {
       case 1.1: { sal = 10.203; break; }
       case 1.3: { sal = 10.522; break; }
       case 1.4: { sal = 10.344; break; }
       case 2.1: { sal = 10.346; break; }
       case 2.4: { sal = 10.352; break; }
       case 4:   { sal =  9.947; break; }
       case 5:   { sal = 10.165; break; }
       case 11:  { sal = 10.107; break; }
       default:  { sal = 0; break; }
      }
    x = parseInt(ed);
    switch (emp)
      {
       case 1.1: { sal = sal + (x *  0.042); break; }
       case 1.3: { sal = sal + (x *  0.027); break; }
       case 1.4: { sal = sal + (x *  0.050); break; } 
       case 2.1: { sal = sal + (x *  0.055); break; }
       case 2.4: { sal = sal + (x *  0.088); break; }
       case 4:   { sal = sal + (x *  0.084); break; }
       case 5:   { sal = sal + (x *  0.052); break; }
       case 11:  { sal = sal + (x *  0.044); break; }
       default:  { sal = 0; break; }
      }    
    if (parseInt(aicp) == 1)
      {
      switch (emp)
        {
         case 1.1: { sal = sal +  0.032; break; }
         case 1.3: { sal = sal +  0.038; break; }
         case 1.4: { sal = sal +  0.014; break; } 
         case 2.1: { sal = sal +  0.051; break; }
         case 2.4: { sal = sal +  0.005; break; }
         case 4:   { sal = sal +  0.048; break; }
         case 5:   { sal = sal +  0.086; break; }
         case 11:  { sal = sal + -0.006; break; }
         default:  { sal = 0; break; }
        }
      }
    x = parseInt(exp);
    switch (emp)
      {
       case 1.1: { sal = sal + (x * 0.163) + (x * x * -0.008); break; }
       case 1.3: { sal = sal + (x * 0.093) + (x * x * -0.003); break; }
       case 1.4: { sal = sal + (x * 0.133) + (x * x * -0.005); break; }
       case 2.1: { sal = sal + (x * 0.063) + (x * x * -0.001); break; }
       case 2.4: { sal = sal + (x * 0.093) + (x * x * -0.003); break; }
       case 4:   { sal = sal + (x * 0.180) + (x * x * -0.009); break; }
       case 5:   { sal = sal + (x * 0.178) + (x * x * -0.011); break; }
       case 11:  { sal = sal + (x * 0.223) + (x * x * -0.011); break; }
       default:  { sal = 0; break; }
      }    
    x = parseInt(sup);
    switch (emp)
      {
         case 1.1: { sal = sal + (x *  0.050); break; }
         case 1.3: { sal = sal + (x *  0.052); break; }
         case 1.4: { sal = sal + (x *  0.051); break; } 
         case 2.1: { sal = sal + (x *  0.047); break; }
         case 2.4: { sal = sal + (x *  0.044); break; }
         case 4:   { sal = sal + (x *  0.054); break; }
         case 5:   { sal = sal + (x *  0.042); break; }
         case 11:  { sal = sal + (x *  0.052); break; }
         default:  { sal = 0; break; }
      }
    if (parseInt(dir) == 1)
      {
       switch (emp)
         {
         case 1.1: { sal = sal + -0.021; break; }
         case 1.3: { sal = sal +  0.029; break; }
         case 1.4: { sal = sal +  0.098; break; } 
         case 2.1: { sal = sal +  0.024; break; }
         case 2.4: { sal = sal +  0.082; break; }
         case 4:   { sal = sal +  0.007; break; }
         case 5:   { sal = sal +  0.100; break; }
         case 11:  { sal = sal +  0; break; }
         default:  { sal = 0; break; }
         }
      }
  }
  if ( sal == 0 )
    {
     document.f.result.value = "not available";
    }
  else
    {
//   sal = Math.round(Math.exp(sal));     rounded twice!
//   document.f.result.value = x2$(sal);
     document.f.result.value = x2$(Math.exp(sal));
    }
}
		
//  ------------------------------------------------------------
		function getvars()
		{
			var msg = "";


			ed = getselect("ed");
			if (ed     == -1) msg += "\n        " + "Highest Degree";

			aicp = getradio("aicp");
			if (aicp   == -1) msg += "\n        " + "AICP";

			exp = getselect("exp");
			if (exp    == -1) msg += "\n        " + "Years in Field";

			emp = getselect("emp");
			if (emp == -1) msg += "\n        " + "Employment Setting";

			sup = getselect("sup");
			if (sup == -1) msg += "\n        " + "Number Supervised";

			dir = getradio("dir");
			if (dir == -1) msg += "\n        " + "Agency Director";


			if (msg != "")
			{	
				msg = "_________________________\n\n" + "Please select response for:\n" + msg
				msg = msg + "\n\n_________________________\n"
  			alert(msg);
  			return false;
			}
			else return true;
		}
//  ------------------------------------------------------------
		function getselect(element)
		{
			for (var i = 0; i < document.f[element].length; i++)
			{
				if (document.f[element].options[i].selected) 
				return document.f[element].options[i].value;
			}
			return -1;
		}

//  ------------------------------------------------------------
		function getradio(element)
		{
			for (var i = 0; i < document.f[element].length; i++)
			{
				if (document.f[element][i].checked) return document.f[element][i].value;
			}
			return -1;
		}

//  ------------------------------------------------------------
		function getcheckbox(element)
		{
			if (document.f[element].checked) return 1;
			return 0;
		}

//  ------------------------------------------------------------
		function x2$(x)
		{
		  x = 100 * Math.floor(0.01 * (50 + x))

		  var res = "";
		  for (var i = 8; i > 0; i--) 
      {
		    var p = Math.pow(10, i);
		    var d = Math.floor(x / p);
		    if (d > 0) 
        {
		      res = res + d;
		      x = x - (d * p);
		    }
		    else if (res != "") res = res + "0";
		    if ((i % 3 == 0) && (i > 0) && (res != ""))
		      res = res + ",";
		  }
		  res = res + x;
		  return "$" + res;
		}
       