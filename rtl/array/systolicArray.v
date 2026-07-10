module systolicArray #(N = 2) (input wire clk, input wire reset, input wire enable, input wire signed [N*8-1:0] a_in, input wire signed [N*8-1:0] b_in, output wire signed [N*N*32-1:0] out); 
    wire signed [7:0] a_wire [0:N-1][0:N-1];
    wire signed [7:0] b_wire [0:N-1][0:N-1];
    wire signed [7:0] a_sel [0:N-1][0:N-1];
    wire signed [7:0] b_sel [0:N-1][0:N-1];
    wire signed [31:0] out_wire [0:N-1][0:N-1];

    genvar i, j;
    generate
        for(i = 0; i < N; i = i + 1) begin : row
            for(j = 0; j < N; j = j +1 ) begin : col
                if (j == 0) begin : a_edge
                    assign a_sel[i][j] = $signed(a_in[i*8 +: 8]);
                end else begin : a_inner
                    assign a_sel[i][j] = a_wire[i][j-1];
                end

                if (i == 0) begin : b_edge
                    assign b_sel[i][j] = $signed(b_in[j*8 +: 8]);
                end else begin : b_inner
                    assign b_sel[i][j] = b_wire[i-1][j];
                end

                processingElement pe(
                    .clk(clk),
                    .reset(reset),
                    .enable(enable),
                    .a_in(a_sel[i][j]),
                    .b_in(b_sel[i][j]),
                    .out(out_wire[i][j]),
                    .a_pass(a_wire[i][j]),
                    .b_pass(b_wire[i][j])
                );
                assign out[(i*N+j)*32 +: 32] = out_wire[i][j];
            end
        end
    endgenerate

endmodule