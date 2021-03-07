from pycompile.parser.parser import Parser


def main():

    parser = Parser("Table")

    code = """"""

    parser.parse(code)

    code = """"""

    parser = Parser("Table", grammar_file="./parser/grammar_files/LL1.paquet.grm", optional=opt)
    parser.parse(code)

    code = """"""

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

class GHIBBERISH in alskjd al j asd a lkj {
    aslkdj laksjd 
    alskd 
    asdm as ma da
    alskd a 
    asd mas 
    a am  lm_l a_d_ lm _dma asl_d m
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