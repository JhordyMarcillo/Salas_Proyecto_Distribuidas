import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { MessageSquare } from "lucide-react";
import { toast } from "sonner";

const Login = () => {
  const navigate = useNavigate();
  const [name, setName] = useState("");
  const [password, setPassword] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!name || !password) {
      toast.error("Please fill in all fields");
      return;
    }

    // usar socket.io para autenticación (envía evento "login")
    import("@/lib/socket").then(({ initSocket }) => {
      const sock = initSocket();

      // manejar respuestas
      const onSuccess = (d: any) => {
        if (d && d.token) {
          localStorage.setItem("chat_token", d.token);
          // guardar usuario para marcar mensajes propios
          localStorage.setItem("chat_user", name);
          // reconectar el socket con token para handshake
          try { initSocket(d.token); } catch (e) { /* ignore */ }
          toast.success("Login successful!");
          navigate("/lobby");
        } else {
          toast.error("Login: respuesta inválida del servidor");
        }
      };

      const onError = (d: any) => {
        toast.error(d && d.msg ? d.msg : "Login failed");
      };

      sock.once("login_success", onSuccess);
      sock.once("login_error", onError);

      // si el socket no está conectado aún, esperar al evento connect
      if (!sock.connected) {
        const onConnect = () => {
          try {
            sock.emit("login", { username: name, password });
          } catch (e) {
            toast.error("Error al emitir login: " + String(e));
          }
        };
        sock.once("connect", onConnect);
        sock.once("connect_error", (err: any) => {
          toast.error("No se pudo conectar al servidor: " + (err && err.message ? err.message : String(err)));
        });
      } else {
        try {
          sock.emit("login", { username: name, password });
        } catch (e) {
          toast.error("Error al emitir login: " + String(e));
        }
      }
    }).catch((e) => {
      toast.error("No se pudo inicializar socket: " + String(e));
    });
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-background px-4">
      <div className="w-full max-w-md space-y-8 animate-fade-in">
        <div className="text-center">
          <div className="flex justify-center mb-4">
            <div className="p-3 bg-card rounded-2xl border border-primary/30 glow-button">
              <MessageSquare className="w-12 h-12 text-primary" />
            </div>
          </div>
          <h1 className="text-4xl font-bold text-primary mb-2">AquaChat</h1>
          <p className="text-muted-foreground">Sign in to continue</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="name" className="text-foreground">Usuario</Label>
              <Input
                id="name"
                type="text"
                placeholder="Tu Usuario"
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="bg-card border-input focus:border-primary transition-colors"
              />
            </div>
            
            <div className="space-y-2">
              <Label htmlFor="password" className="text-foreground">Contraseña</Label>
              <Input
                id="password"
                type="password"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="bg-card border-input focus:border-primary transition-colors"
              />
            </div>
          </div>

          <Button 
            type="submit" 
            className="w-full glow-button bg-primary hover:bg-accent text-primary-foreground font-semibold"
          >
            Inicar
          </Button>

          <p className="text-center text-muted-foreground text-sm">
            No tienes cuenta aun? que esperas{" "}
            <button
              type="button"
              onClick={() => navigate("/register")}
              className="text-primary hover:text-accent transition-colors font-medium"
            >
              Registra te
            </button>
          </p>
        </form>
      </div>
    </div>
  );
};

export default Login;
