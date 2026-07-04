module processingElement (input wire signed [7:0] in1, input wire signed [7:0] in2, input wire clk, input wire reset, input wire enable, output reg signed [31:0] out);
    
    reg signed [15:0] product;
    parameter MAX_VALUE = 32'h7FFFFFFF;
    parameter MIN_VALUE = 32'sh80000000;

    always @(posedge clk or posedge reset) 
    begin
        if (reset) begin
            out <= 0;
        end
        else if (enable) begin
            product = in1 * in2;
            if (out + product > MAX_VALUE)
                out <= MAX_VALUE;
            else if (out + product < MIN_VALUE)
                out <= MIN_VALUE;
            else
                out <= out + product;
        end
    end


endmodule