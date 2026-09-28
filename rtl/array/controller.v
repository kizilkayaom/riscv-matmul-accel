module controller (
    input wire clk,
    input wire reset,
    input wire start,
    input [31:0] a_matrix,
    input [31:0] b_matrix,

    output wire busy,
    output wire done,
    output wire [127:0] out
);


localparam IDLE  = 3'd0,
            CLEAR = 3'd1,
            STEP0 = 3'd2,
            STEP1 = 3'd3,
            STEP2 = 3'd4,
            STEP3 = 3'd5,
            DONE  = 3'd6;

reg [2:0] state;
reg [31:0] a_saved;
reg [31:0] b_saved;
reg [15:0] array_a;
reg [15:0] array_b;
wire array_reset;
wire array_enable;

always @(posedge clk or posedge reset) begin
    if (reset) begin
        state <= IDLE;
        a_saved <= 32'b0;
        b_saved <= 32'b0;
    end else begin
        case (state)
            IDLE:
                if (start) begin
                    state <= CLEAR;
                    a_saved <= a_matrix;
                    b_saved <= b_matrix;
            end
            
            CLEAR: state <= STEP0;
            STEP0: state <= STEP1;
            STEP1: state <= STEP2;
            STEP2: state <= STEP3;
            STEP3: state <= DONE;

            DONE:
                if (start) begin
                    state <= CLEAR;
                    a_saved <= a_matrix;
                    b_saved <= b_matrix;
            end

            default: state <= IDLE;
        endcase
    end
end

assign busy = (state == CLEAR) ||
              (state == STEP0) || (state == STEP1) ||
              (state == STEP2) || (state == STEP3);

assign done = (state == DONE);

assign array_reset = reset || (state == CLEAR);

assign array_enable = !reset &&
                      ((state == STEP0) || (state == STEP1) ||
                       (state == STEP2) || (state == STEP3));

always @(*) begin
    array_a = 16'b0;
    array_b = 16'b0;

    case (state)
        STEP0: begin
            array_a = {8'b0, a_saved[7:0]};
            array_b = {8'b0, b_saved[7:0]};
        end

        STEP1: begin
            array_a = {a_saved[23:16], a_saved[15:8]};
            array_b = {b_saved[15:8], b_saved[23:16]};
        end

        STEP2: begin
            array_a = {a_saved[31:24], 8'b0};
            array_b = {b_saved[31:24], 8'b0};
        end

        default: begin
        end
    endcase
end

systolicArray #(.N(2)) array_inst (
    .clk(clk),
    .reset(array_reset),
    .enable(array_enable),
    .a_in(array_a),
    .b_in(array_b),
    .out(out)
);

endmodule