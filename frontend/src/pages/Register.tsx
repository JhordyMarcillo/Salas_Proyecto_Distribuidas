import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { MessageSquare } from "lucide-react";
import { toast } from "sonner";

const Register = () => {
  const navigate = useNavigate();
  const [name, setName] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    if (!name || !password || !confirmPassword) {
      toast.error("Please fill in all fields");
      return;
    }

    if (password !== confirmPassword) {
      toast.error("Passwords don't match");
      return;
    }

    // Usar socket para registrar usuario en backend
    import("@/lib/socket").then(({ initSocket }) => {
      // Inicializar socket y reconectar con token si es devuelto
      const sock = initSocket();
      sock.once("register_success", (d: any) => {
        if (d && d.token) {
          localStorage.setItem("chat_token", d.token);
          localStorage.setItem("chat_user", name);
          // reconectar el socket con el token en handshake
          try { initSocket(d.token); } catch (e) { /* ignore */ }
          toast.success("Account created successfully!");
          navigate("/lobby");
        } else {
          toast.error("Registro: respuesta inválida del servidor");
        }
      });
      sock.once("register_error", (d: any) => {
        toast.error(d && d.msg ? d.msg : "Register failed");
      });

      // usamos el campo email como username en este proyecto
      sock.emit("register", { username: name, password });
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
          <h1 className="text-4xl font-bold text-primary mb-2">Join AquaChat</h1>
          <p className="text-muted-foreground">Create una cuenta</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="name" className="text-foreground">Usuario</Label>
              <Input
                id="name"
                type="text"
                placeholder="Usuario"
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

            <div className="space-y-2">
              <Label htmlFor="confirmPassword" className="text-foreground">Confirmar Contraseña</Label>
              <Input
                id="confirmPassword"
                type="password"
                placeholder="••••••••"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                className="bg-card border-input focus:border-primary transition-colors"
              />
            </div>
          </div>

          <Button 
            type="submit" 
            className="w-full glow-button bg-primary hover:bg-accent text-primary-foreground font-semibold"
          >
            Crear la cuenta
          </Button>

          <p className="text-center text-muted-foreground text-sm">
            Ya tienes cuenta? Inicia{" "}
            <button
              type="button"
              onClick={() => navigate("/login")}
              className="text-primary hover:text-accent transition-colors font-medium"
            >
              Sesión
            </button>
          </p>
        </form>
      </div>
    </div>
  );
};

export default Register;
