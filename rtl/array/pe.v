module processingElement (input wire signed [7:0] a_in, input wire signed [7:0] b_in, input wire clk, input wire reset, input wire enable, output reg signed [31:0] out, output reg signed [7:0] a_pass, output reg signed [7:0] b_pass);
    
    reg signed [15:0] product;
    parameter signed [31:0] MAX_VALUE = 32'sh7FFFFFFF;
    parameter signed [31:0] MIN_VALUE = 32'sh80000000;
    reg signed [32:0] sum;

    always @(posedge clk or posedge reset) 
    begin
        if (reset) begin
            out <= 0;
            a_pass <= 0;
            b_pass <= 0;
        end
        else if (enable) begin
            product = a_in * b_in;
            sum = $signed({out[31], out}) + $signed({{17{product[15]}}, product});
            if (sum > MAX_VALUE)
                out <= MAX_VALUE;
            else if (sum < MIN_VALUE)
                out <= MIN_VALUE;
            else
                out <= sum;
            a_pass <= a_in;
            b_pass <= b_in;
        end
    end


endmodule