import { useState, useEffect } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ArrowLeft, Send } from "lucide-react";
import { ScrollArea } from "@/components/ui/scroll-area";
import { useToast } from "@/hooks/use-toast";

interface Message {
  id: string;
  user: string;
  text: string;
  timestamp: Date;
  isOwn: boolean;
}

const ChatRoom = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const { toast } = useToast();
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputMessage, setInputMessage] = useState("");

  const roomName = id === "1" ? "General Chat" : `Room ${id}`;

  // conexión a backend via Socket.IO
  useEffect(() => {
    let mounted = true;
    const room = id ?? "default";
    const token = localStorage.getItem("chat_token");

    // cargar historial via REST
    import("@/lib/socket").then(({ apiUrl, initSocket }) => {
      // obtener mensajes del historial
      fetch(`${apiUrl}/rooms/${room}/messages`)
        .then((r) => r.json())
        .then((data) => {
          if (!mounted) return;
          const msgs = (data.messages || []).map((m: any, idx: number) => ({
            id: String(idx) + (m.timestamp || ""),
            user: m.username || "",
            text: m.msg || "",
            timestamp: m.timestamp ? new Date(m.timestamp) : new Date(),
            isOwn: (m.username || "") === (localStorage.getItem("chat_user") || "You")
          }));
          setMessages(msgs);
        })
        .catch(() => {
          // si falla, mantener vacío
        });

      const sock = initSocket(token ?? undefined);

      // manejar nuevos mensajes
      const onMessage = (d: any) => {
        if (!mounted) return;
        if (d && d.room && String(d.room) === String(room)) {
          const m: Message = {
            id: Date.now().toString(),
            user: d.username || "",
            text: d.msg || "",
            timestamp: d.timestamp ? new Date(d.timestamp) : new Date(),
            isOwn: (d.username || "") === (localStorage.getItem("chat_user") || "You")
          };
          setMessages((prev) => [...prev, m]);
        }
      };

      sock.on("message", onMessage);

      // Unirse a la sala al montar
      sock.emit("join", { token: token, room });

      return () => {
        mounted = false;
        try {
          sock.emit("leave", { token: token, room });
        } catch (e) {}
        sock.off("message", onMessage);
      };
    });
  }, [id, toast]);

  // Notificación al entrar a la sala
  useEffect(() => {
    toast({
      title: "Entraste a la sala",
      description: `Bienvenido a ${roomName}`,
    });

    // Notificación al salir (cleanup)
    return () => {
      toast({
        title: "Saliste de la sala",
        description: `Has salido de ${roomName}`,
      });
    };
  }, [id, roomName, toast]);

  const handleSendMessage = (e: React.FormEvent) => {
    e.preventDefault();
    if (inputMessage.trim()) {
      const room = id ?? "default";
      const token = localStorage.getItem("chat_token");
      // emitir al servidor
      import("@/lib/socket").then(({ getSocket }) => {
        const s = getSocket();
        try {
          s?.emit("send_message", { token: token, room: room, msg: inputMessage });
        } catch (e) {
          // si no hay socket, mostrar localmente
          const newMessage: Message = {
            id: Date.now().toString(),
            user: "You",
            text: inputMessage,
            timestamp: new Date(),
            isOwn: true,
          };
          setMessages((prev) => [...prev, newMessage]);
        }
      });

      setInputMessage("");
    }
  };

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit" });
  };

  return (
    <div className="h-screen flex flex-col bg-background">
      <header className="border-b border-border bg-card/50 backdrop-blur-sm">
        <div className="container mx-auto px-4 py-4 flex items-center gap-4">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => navigate("/lobby")}
            className="hover:bg-primary/10"
          >
            <ArrowLeft className="w-5 h-5" />
          </Button>
          <div>
            <h1 className="text-xl font-bold text-primary">{roomName}</h1>
            <p className="text-xs text-muted-foreground">42 members online</p>
          </div>
        </div>
      </header>

      <ScrollArea className="flex-1 px-4">
        <div className="container mx-auto max-w-4xl py-6 space-y-4">
          {messages.map((message) => (
            <div
              key={message.id}
              className={`flex ${message.isOwn ? "justify-end" : "justify-start"} animate-fade-in`}
            >
              <div className={`max-w-[70%] space-y-1 ${message.isOwn ? "items-end" : "items-start"} flex flex-col`}>
                {!message.isOwn && (
                  <span className="text-xs text-muted-foreground font-medium px-3">{message.user}</span>
                )}
                <div className={`px-4 py-3 ${message.isOwn ? "chat-bubble-user" : "chat-bubble-other"}`}>
                  <p className="text-sm">{message.text}</p>
                </div>
                <span className="text-xs text-muted-foreground px-3">{formatTime(message.timestamp)}</span>
              </div>
            </div>
          ))}
        </div>
      </ScrollArea>

      <div className="border-t border-border bg-card/50 backdrop-blur-sm">
        <form onSubmit={handleSendMessage} className="container mx-auto max-w-4xl px-4 py-4">
          <div className="flex gap-2">
            <Input
              type="text"
              placeholder="Type a message..."
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              className="flex-1 bg-background border-input focus:border-primary"
            />
            <Button 
              type="submit" 
              className="glow-button bg-primary hover:bg-accent text-primary-foreground px-6"
            >
              <Send className="w-4 h-4" />
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default ChatRoom;
