from pycompile.parser.parser import Parser


def main():

    code = "main { test.thats().ok = 5 ; }"
    parser = Parser()
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
printArray(integer arr[], integer size) : void 
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

    parser = Parser()
    parser.parse(code)

    print('Finished')


if __name__ == '__main__':
    main()