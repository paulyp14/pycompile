from pycompile.parser.parser import Parser


def main():

    opt = {
        'calgaryTableFile': './parser/grammar_files/ucalgary_parse_table.html',
        'calgaryFirstAndFollow': './parser/grammar_files/ucalgary_first_follow.html'
    }
    parser = Parser("Table", grammar_file="./parser/grammar_files/LL1.paquet.grm", optional=opt)

    code = "main { test.thats[6][16+8] = 5 ; }"
    parser.parse(code)

    code = """/* sort the array */
func bubbleSort(integer arr[], integer size) : void 
{
  var 
  {
    integer n;
    integer i;
    integer j;
    integer temp; 
  }
  n = size;
  i = 0;
  j = 0;
  temp = 0;
  while (i < n-1) { 
    while (j < n-i-1) {
      if (arr[j] > arr[j+1]) 
        then {
          // swap temp and arr[i]
          temp = arr[j];
          arr[j] = arr[j+1];
          arr[j+1] = temp;
        } else ;
        j = j+1;
      };
    i = i+1;
  };
}
   
/* Print the array */
func printArray(integer arr[], integer size) : void 
{
  var
  {
    integer n;
    integer i; 
  }
  n = size;
  i = 0; 
  while (i<n) { 
    write(arr[i]);
      i = i+1;
  };
} 

// main funtion to test above
main 
{
  var 
  {
    integer arr[7]; 
  }
  arr[0] = 64;
  arr[1] = 34;
  arr[2] = 25;
  arr[3] = 12;
  arr[4] = 22;
  arr[5] = 11;
  arr[6] = 90;
  printarray(arr, 7); 
  bubbleSort(arr, 7);
  printarray(arr, 7); 
}"""



    parser = Parser("Table", grammar_file="./parser/grammar_files/LL1.paquet.grm", optional=opt)
    parser.parse(code)

    code = """
// ====== Class declarations ====== //
class POLYNOMIAL {
	public func evaluate(float x) : float;
};

class LINEAR inherits POLYNOMIAL {
	private float a;
	private float b;
	
	public func build(float A, float B) : LINEAR;
	public func evaluate(float x) : float;
};

class QUADRATIC inherits POLYNOMIAL {
	private float a;
	private float b;
	private float c;
	
	public func build(float A, float B, float C) : QUADRATIC;
	public func evaluate(float x) : float;
};

// ====== Function Definitions ====== //
func POLYNOMIAL::evaluate(float x) : float
{
  return (0);
}

func LINEAR::evaluate(float x) : float 
{
  var
  {
    float result;
  }
  result = 0.0;
  result = a * x + b;
  return (result);
}
  
func QUADRATIC::evaluate(float x) : float
{
  var    
  {
    float result;
  }
  //Using Horner's method
  result = a;
  result = result * x + b;
  result = result * x + c;
  return (result);
}
  
func LINEAR::build(float A, float B) : LINEAR 
{
  var 
  {
    LINEAR new_function;
  }
  new_function.a = A;
  new_function.b = B;
  return (new_function);
}
  
func QUADRATIC::build(float A, float B, float C) : QUADRATIC
{
  var
  {
    QUADRATIC new_function;
  }
  new_function.a = A;
  new_function.b = B;
  new_function.c = C;
  return (new_function);
}
  

// ====== main ====== //
main
{
  var
  {
    linear f1;
    quadratic f2;
    integer counter;
  }
  f1 = f1.build(2, 3.5);
  f2 = f2.build(-2.0, 1.0, 0.0);
  counter = 1;
	
  while(counter <= 10)
  {
    write(counter);
    write(f1.evaluate(counter));
    write(f2.evaluate(counter));
  };
}"""

    parser = Parser("Table", grammar_file="./parser/grammar_files/LL1.paquet.grm", optional=opt)
    parser.parse(code)

    print('Finished')


if __name__ == '__main__':
    main()