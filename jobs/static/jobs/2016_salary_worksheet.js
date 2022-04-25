//
//  2016worksheet.js   APA/AICP 2016 Salary Worksheet   #17900    05/20/2016
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
    emp = parseInt(emp);
    switch (emp)
      {
       case  1: { sal = 10.402; break; }
       case  2: { sal = 10.155; break; }
       case  3: { sal = 10.538; break; }  
       case  4: { sal = 10.094; break; }  
       case  5: { sal = 10.327; break; }  
//     case  6: { sal = 10.459; break; }  
       case  7: { sal = 10.251; break; }  
       case  8: { sal = 10.198; break; }  
       case  9: { sal = 10.449; break; }
       case 10: { sal = 10.143; break; }
       default: { sal = 0; break; }
      }
    x = parseInt(ed);
    switch (emp)
      {
       case  1: { sal = sal + (x *  0.035); break; }
       case  2: { sal = sal + (x *  0.040); break; }
       case  3: { sal = sal + (x *  0.014); break; } 
       case  4: { sal = sal + (x *  0.052); break; }
       case  5: { sal = sal + (x *  0.058); break; }
//     case  6: { sal = sal + (x *  0.039); break; }
       case  7: { sal = sal + (x *  0.006); break; }
       case  8: { sal = sal + (x *  0.015); break; }
       case  9: { sal = sal + (x *  0.032); break; }
       case 10: { sal = sal + (x *  0.047); break; }
       default: { sal = sal * 0; break; }
      }    
    if (parseInt(aicp) == 1)
      {
      switch (emp)
        {
         case  1: { sal = sal + 0.043; break; }
         case  2: { sal = sal - 0.005; break; } 
         case  3: { sal = sal + 0.015; break; }
         case  4: { sal = sal + 0.023; break; }
         case  5: { sal = sal + 0.036; break; }
//       case  6: { sal = sal + 0.087; break; }
         case  7: { sal = sal + 0.060; break; }
         case  8: { sal = sal - 0.035; break; }
         case  9: { sal = sal + 0.052; break; }
         case 10: { sal = sal + 0.012; break; }
         default: { sal = sal * 0; break; }
        }
      }
    x = parseInt(exp);
    switch (emp)
      {
       case  1: { sal = sal + (x * 0.088) + (x * x * -0.003); break; }
       case  2: { sal = sal + (x * 0.181) + (x * x * -0.009); break; }
       case  3: { sal = sal + (x * 0.111) + (x * x * -0.004); break; }
       case  4: { sal = sal + (x * 0.140) + (x * x * -0.007); break; }
       case  5: { sal = sal + (x * 0.096) + (x * x * -0.003); break; }
//     case  6: { sal = sal + (x * 0.022) + (x * x *  0.002); break; }
       case  7: { sal = sal + (x * 0.139) + (x * x * -0.006); break; }
       case  8: { sal = sal + (x * 0.201) + (x * x * -0.010); break; }
       case  9: { sal = sal + (x * 0.106) + (x * x * -0.005); break; }
       case 10: { sal = sal + (x * 0.189) + (x * x * -0.008); break; }
       default: { sal = sal * 0; break; }
      }    
    x = parseInt(sup);
    switch (emp)
      {
       case  1: { sal = sal + (x *  0.053); break; }
       case  2: { sal = sal + (x *  0.052); break; }
       case  3: { sal = sal + (x *  0.054); break; }
       case  4: { sal = sal + (x *  0.049); break; }
       case  5: { sal = sal + (x *  0.046); break; }
//     case  6: { sal = sal + (x *  0.049); break; }
       case  7: { sal = sal + (x *  0.049); break; }
       case  8: { sal = sal + (x *  0.058); break; }
       case  9: { sal = sal + (x *  0.039); break; }
       case 10: { sal = sal + (x *  0.060); break; }
       default: { sal = sal * 0; break; }
      }
    if (parseInt(dir) == 1)
      {
       switch (emp)
         {
          case  1: { sal = sal + 0.027; break; }
          case  2: { sal = sal + 0.049; break; }
          case  3: { sal = sal + 0.125; break; }
          case  4: { sal = sal - 0.034; break; }
          case  5: { sal = sal + 0.052; break; }
//        case  6: { sal = sal + 0.054; break; }
          case  7: { sal = sal + 0.119; break; }
          case  8: { sal = sal + 0.025; break; }
          case  9: { sal = sal + 0.075; break; }
          case 10: { sal = sal + 0; break; }
          default: { sal = sal * 0; break; }
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
       