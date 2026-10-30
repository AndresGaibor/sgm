/* priority: P2 */
filename listing pipe 'echo placeholder';
data work.output; infile listing; input line $80.; run;
