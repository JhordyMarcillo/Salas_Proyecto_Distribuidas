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

const mockMessages: Message[] = [
  { id: "1", user: "Alice", text: "Hey everyone!", timestamp: new Date(Date.now() - 300000), isOwn: false },
  { id: "2", user: "You", text: "Hi Alice! How's it going?", timestamp: new Date(Date.now() - 240000), isOwn: true },
  { id: "3", user: "Bob", text: "Great to be here!", timestamp: new Date(Date.now() - 180000), isOwn: false },
  { id: "4", user: "You", text: "Welcome Bob!", timestamp: new Date(Date.now() - 120000), isOwn: true },
];

const ChatRoom = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const { toast } = useToast();
  const [messages, setMessages] = useState<Message[]>(mockMessages);
  const [inputMessage, setInputMessage] = useState("");

  const roomName = id === "1" ? "General Chat" : `Room ${id}`;

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
      const newMessage: Message = {
        id: Date.now().toString(),
        user: "You",
        text: inputMessage,
        timestamp: new Date(),
        isOwn: true,
      };
      setMessages([...messages, newMessage]);
      setInputMessage("");

      // Simular mensaje de otro usuario después de 2 segundos
      setTimeout(() => {
        const otherMessage: Message = {
          id: (Date.now() + 1).toString(),
          user: "Alice",
          text: "¡Recibí tu mensaje!",
          timestamp: new Date(),
          isOwn: false,
        };
        setMessages(prev => [...prev, otherMessage]);
        
        // Notificación de mensaje nuevo
        toast({
          title: "Nuevo mensaje",
          description: `${otherMessage.user}: ${otherMessage.text}`,
        });
      }, 2000);
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
