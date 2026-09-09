import subprocess, sys
tpl = subprocess.run(["ollama","show","--template","qwen3:14b"],capture_output=True,text=True).stdout
orig = tpl
# 1) always append /no_think to the last user message
a_old = '''{{- if and $.IsThinkSet (eq $i $lastUserIdx) }}
   {{- if $.Think -}}
      {{- " "}}/think
   {{- else -}}
      {{- " "}}/no_think
   {{- end -}}
{{- end }}'''
a_new = '''{{- if (eq $i $lastUserIdx) }}
   {{- " "}}/no_think
{{- end }}'''
assert a_old in tpl, "PATCH A NOT FOUND"
tpl = tpl.replace(a_old, a_new)
# 2) always prefill an empty think block on the assistant turn
b_old = '{{ if and $.IsThinkSet (not $.Think) -}}'
b_new = '{{ if true -}}'
assert b_old in tpl, "PATCH B NOT FOUND"
tpl = tpl.replace(b_old, b_new)
assert tpl != orig
mf = 'FROM qwen3:14b\nPARAMETER temperature 0.2\nPARAMETER seed 111\nPARAMETER num_ctx 32768\nTEMPLATE """' + tpl + '"""\n'
open("/root/Modelfile.nothink","w").write(mf)
print("wrote /root/Modelfile.nothink (%d bytes)"%len(mf))
