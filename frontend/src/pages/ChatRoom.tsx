import { useState, useEffect, useRef } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ArrowLeft, Send, Image as ImageIcon, FileText, X, Download } from "lucide-react";
import { ScrollArea } from "@/components/ui/scroll-area";
import { useToast } from "@/hooks/use-toast";

interface Message {
  id: string;
  user: string;
  text: string;
  image?: string;
  file?: { name: string; data: string; type: string };
  timestamp: Date;
  isOwn: boolean;
}

const ChatRoom = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const { toast } = useToast();
  const [messages, setMessages] = useState<Message[]>([]);
  const [usersOnline, setUsersOnline] = useState<string[]>([]);
  const [inputMessage, setInputMessage] = useState("");
  const [selectedImage, setSelectedImage] = useState<string | null>(null);
  const [selectedFile, setSelectedFile] = useState<{ name: string; data: string; type: string } | null>(null);
  const imageInputRef = useRef<HTMLInputElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const roomName = id ? decodeURIComponent(id) : "Room";

  // conexión a backend via Socket.IO
  useEffect(() => {
    let mounted = true;
    const room = id ?? "default";
    const token = localStorage.getItem("chat_token");

    // cargar historial via REST
    import("@/lib/socket").then(({ apiUrl, initSocket }) => {
      // obtener mensajes del historial
      fetch(`${apiUrl}/rooms/${encodeURIComponent(room)}/messages`)
        .then((r) => r.json())
        .then((data) => {
          if (!mounted) return;
          const msgs = (data.messages || []).map((m: any, idx: number) => ({
            id: String(idx) + (m.timestamp || ""),
            user: m.username || "",
            text: m.msg || "",
            image: m.image || undefined,
            file: m.file || undefined,
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
            image: d.image || undefined,
            file: d.file || undefined,
            timestamp: d.timestamp ? new Date(d.timestamp) : new Date(),
            isOwn: (d.username || "") === (localStorage.getItem("chat_user") || "You")
          };
          setMessages((prev) => [...prev, m]);
          // añadir usuario al listado en linea
          const u = d.username || "";
          if (u) setUsersOnline((prev) => (prev.includes(u) ? prev : [...prev, u]));
        }
      };

      sock.on("message", onMessage);

      // manejar eventos de estado (join/leave)
      const onStatus = (d: any) => {
        if (!mounted) return;
        const msg = d && d.msg ? d.msg : "";
        // formatos esperados: "<username> se unió a <room>", "<username> salió de <room>", "<username> desconectado"
        try {
          if (msg.includes(" se unió a ")) {
            const username = msg.split(" se unió a ")[0];
            if (username) setUsersOnline((prev) => (prev.includes(username) ? prev : [...prev, username]));
          } else if (msg.includes(" salió de ")) {
            const username = msg.split(" salió de ")[0];
            if (username) setUsersOnline((prev) => prev.filter((x) => x !== username));
          } else if (msg.includes(" desconectado")) {
            const username = msg.split(" desconectado")[0];
            if (username) setUsersOnline((prev) => prev.filter((x) => x !== username));
          }
        } catch (e) {
          // ignore parse errors
        }
      };

      sock.on("status", onStatus);

      // eventos estructurados de presencia (backend Option A)
      const onUserJoined = (d: any) => {
        if (!mounted) return;
        try {
          if (!d) return;
          const username = d.username || "";
          const r = d.room || room;
          if (String(r) !== String(room)) return;
          if (username) setUsersOnline((prev) => (prev.includes(username) ? prev : [...prev, username]));
        } catch (e) {}
      };

      const onUserLeft = (d: any) => {
        if (!mounted) return;
        try {
          if (!d) return;
          const username = d.username || "";
          const r = d.room || room;
          if (String(r) !== String(room)) return;
          if (username) setUsersOnline((prev) => prev.filter((x) => x !== username));
        } catch (e) {}
      };

      const onUserDisconnected = (d: any) => {
        if (!mounted) return;
        try {
          if (!d) return;
          const username = d.username || "";
          // si payload incluye room, comprobar que sea la misma; si no, remover de la lista de todas formas
          const r = d.room;
          if (r && String(r) !== String(room)) return;
          if (username) setUsersOnline((prev) => prev.filter((x) => x !== username));
        } catch (e) {}
      };

      sock.on("user_joined", onUserJoined);
      sock.on("user_left", onUserLeft);
      sock.on("user_disconnected", onUserDisconnected);

      // Unirse a la sala al montar
      sock.emit("join", { token: token, room });

      return () => {
        mounted = false;
        try {
          sock.emit("leave", { token: token, room });
        } catch (e) {}
        sock.off("message", onMessage);
        sock.off("status", onStatus);
        sock.off("user_joined", onUserJoined);
        sock.off("user_left", onUserLeft);
        sock.off("user_disconnected", onUserDisconnected);
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
    if (inputMessage.trim() || selectedImage || selectedFile) {
      const room = id ?? "default";
      const token = localStorage.getItem("chat_token");
      // emitir al servidor
      import("@/lib/socket").then(({ getSocket }) => {
        const s = getSocket();
        try {
          s?.emit("send_message", { 
            token: token, 
            room: room, 
            msg: inputMessage,
            image: selectedImage || undefined,
            file: selectedFile || undefined
          });
        } catch (e) {
          // si no hay socket, mostrar localmente
          const newMessage: Message = {
            id: Date.now().toString(),
            user: "You",
            text: inputMessage,
            image: selectedImage || undefined,
            file: selectedFile || undefined,
            timestamp: new Date(),
            isOwn: true,
          };
          setMessages((prev) => [...prev, newMessage]);
        }
      });

      setInputMessage("");
      removeSelectedImage();
      removeSelectedFile();
    }
  };

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit" });
  };

  const handleImageSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      const validImageTypes = ["image/jpeg", "image/png", "image/gif", "image/webp"];
      if (!validImageTypes.includes(file.type)) {
        toast({
          title: "Formato no válido",
          description: "Por favor selecciona una imagen (JPG, PNG, GIF o WebP)",
          variant: "destructive",
        });
        return;
      }

      if (file.size > 5 * 1024 * 1024) {
        toast({
          title: "Archivo muy grande",
          description: "La imagen no debe pesar más de 5MB",
          variant: "destructive",
        });
        return;
      }

      const reader = new FileReader();
      reader.onload = (event) => {
        const base64String = event.target?.result as string;
        setSelectedImage(base64String);
      };
      reader.readAsDataURL(file);
    }
  };

  const removeSelectedImage = () => {
    setSelectedImage(null);
    if (imageInputRef.current) {
      imageInputRef.current.value = "";
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      const maxSize = 10 * 1024 * 1024; // 10MB para archivos
      if (file.size > maxSize) {
        toast({
          title: "Archivo muy grande",
          description: "El archivo no debe pesar más de 10MB",
          variant: "destructive",
        });
        return;
      }

      const reader = new FileReader();
      reader.onload = (event) => {
        const base64String = event.target?.result as string;
        setSelectedFile({
          name: file.name,
          data: base64String,
          type: file.type,
        });
      };
      reader.readAsDataURL(file);
    }
  };

  const removeSelectedFile = () => {
    setSelectedFile(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  const downloadFile = (fileData: string, fileName: string) => {
    const link = document.createElement("a");
    link.href = fileData;
    link.download = fileName;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
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
            <p className="text-xs text-muted-foreground">
              {(() => {
                const users = Array.from(new Set(usersOnline.filter(Boolean)));
                if (users.length === 0) return "No hay usuarios conectados";
                return `${users.length} usuario${users.length > 1 ? "s" : ""} en línea: ${users.join(", ")}`;
              })()}
            </p>
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
                  {message.image && (
                    <img src={message.image} alt="Imagen compartida" className="max-w-xs rounded-lg mb-2" />
                  )}
                  {message.file && (
                    <div className="flex items-center gap-2 mb-2 bg-secondary/20 p-2 rounded">
                      <FileText className="w-4 h-4 flex-shrink-0" />
                      <span className="text-sm truncate flex-1">{message.file.name}</span>
                      <Button
                        size="sm"
                        variant="ghost"
                        className="p-1 h-6 w-6"
                        onClick={() => downloadFile(message.file!.data, message.file!.name)}
                        title="Descargar archivo"
                      >
                        <Download className="w-3 h-3" />
                      </Button>
                    </div>
                  )}
                  {message.text && <p className="text-sm">{message.text}</p>}
                </div>
                <span className="text-xs text-muted-foreground px-3">{formatTime(message.timestamp)}</span>
              </div>
            </div>
          ))}
        </div>
      </ScrollArea>

      <div className="border-t border-border bg-card/50 backdrop-blur-sm">
        <form onSubmit={handleSendMessage} className="container mx-auto max-w-4xl px-4 py-4 space-y-3">
          {selectedImage && (
            <div className="relative inline-block">
              <img src={selectedImage} alt="Preview" className="max-h-32 rounded-lg" />
              <Button
                type="button"
                size="icon"
                variant="destructive"
                className="absolute -top-2 -right-2 h-6 w-6"
                onClick={removeSelectedImage}
              >
                <X className="w-3 h-3" />
              </Button>
            </div>
          )}
          {selectedFile && (
            <div className="flex items-center gap-2 bg-secondary/20 p-3 rounded-lg">
              <FileText className="w-5 h-5 flex-shrink-0" />
              <span className="text-sm truncate flex-1">{selectedFile.name}</span>
              <Button
                type="button"
                size="icon"
                variant="destructive"
                className="h-6 w-6"
                onClick={removeSelectedFile}
              >
                <X className="w-3 h-3" />
              </Button>
            </div>
          )}
          <div className="flex gap-2">
            <Input
              type="text"
              placeholder="Escribe el tu mensaje..."
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              className="flex-1 bg-background border-input focus:border-primary"
            />
            <input
              ref={imageInputRef}
              type="file"
              accept="image/*"
              onChange={handleImageSelect}
              className="hidden"
            />
            <input
              ref={fileInputRef}
              type="file"
              onChange={handleFileSelect}
              className="hidden"
            />
            <Button
              type="button"
              variant="outline"
              size="icon"
              onClick={() => imageInputRef.current?.click()}
              className="hover:bg-primary/10"
              title="Subir imagen"
            >
              <ImageIcon className="w-4 h-4" />
            </Button>
            <Button
              type="button"
              variant="outline"
              size="icon"
              onClick={() => fileInputRef.current?.click()}
              className="hover:bg-primary/10"
              title="Subir archivo"
            >
              <FileText className="w-4 h-4" />
            </Button>
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
