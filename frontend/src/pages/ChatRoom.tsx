import { useState, useEffect, useRef } from "react";
import { Dialog } from "@/components/ui/dialog";
import { useNavigate, useParams } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ArrowLeft, Send, Image as ImageIcon, FileText, X, Download, ExternalLink } from "lucide-react";
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
  const bottomRef = useRef<HTMLDivElement>(null);

  // Estado para tipo de sala y PIN
  const [roomType, setRoomType] = useState<string>("text");
  const [pinInput, setPinInput] = useState("");
  const [pinError, setPinError] = useState("");
  
  const room = id ?? "default";
  const hasSavedPin = localStorage.getItem(`pin_${room}`);
  const [showPinDialog, setShowPinDialog] = useState(!hasSavedPin);

  const roomName = id ? decodeURIComponent(id) : "Room";

  // conexión a backend via Socket.IO y obtención de tipo de sala
  useEffect(() => {
    let mounted = true;
    const token = localStorage.getItem("chat_token");

    import("@/lib/socket").then(({ apiUrl, initSocket }) => {
      // obtener info de la sala (tipo y pin)
      fetch(`${apiUrl}/rooms`)
        .then((r) => r.json())
        .then((data) => {
          if (!mounted) return;
          const found = (data.rooms || []).find((r: any) => r.name === room);
          if (found) {
            setRoomType(found.type || "text");
          }
        });

      // obtener mensajes del historial
      fetch(`${apiUrl}/rooms/${encodeURIComponent(room)}/messages`)
        .then((r) => r.json())
        .then((data) => {
          if (!mounted) return;
          const msgs = (data.messages || []).map((m: any, idx: number) => ({
            id: m._id && m._id.$oid ? m._id.$oid : String(idx),
            user: m.username || "",
            text: m.msg || "",
            image: m.file_url && m.file_url.match(/\.(jpg|jpeg|png|gif|webp)$/i) ? m.file_url : undefined,
            file: m.file_url && !m.file_url.match(/\.(jpg|jpeg|png|gif|webp)$/i) ? {
              name: m.original_filename || "archivo",
              data: m.file_url,
              type: "url"
            } : undefined,
            timestamp: m.timestamp ? new Date(m.timestamp) : new Date(),
            isOwn: (m.username || "") === (localStorage.getItem("chat_user") || "You")
          }));
          setMessages(msgs);
        })
        .catch(() => {});

      const sock = initSocket(token ?? undefined);

      // manejar nuevos mensajes
      const onMessage = (d: any) => {
        if (!mounted) return;
        if (d && d.room && String(d.room) === String(room)) {
          let tsRaw = d.timestamp;
          if (d.timestamp && d.timestamp.$date) {
            tsRaw = d.timestamp.$date;
          }
          const m: Message = {
            id: Date.now().toString(),
            user: d.username || "",
            text: d.msg || "",
            image: d.file_url && d.file_url.match(/\.(jpg|jpeg|png|gif|webp)$/i) ? d.file_url : undefined,
            file: d.file_url && !d.file_url.match(/\.(jpg|jpeg|png|gif|webp)$/i) ? {
              name: d.original_filename || "archivo",
              data: d.file_url,
              type: "url"
            } : undefined,
            timestamp: d.timestamp ? new Date(d.timestamp) : new Date(),
            isOwn: (d.username || "") === (localStorage.getItem("chat_user") || "You")
          };
          setMessages((prev) => [...prev, m]);
          if (!m.isOwn) {
            toast({
              title: `Nuevo mensaje de ${m.user}`,
              description: m.text.length > 50 ? m.text.substring(0, 50) + "..." : m.text,
            });
          }
          const u = d.username || "";
          if (u) setUsersOnline((prev) => (prev.includes(u) ? prev : [...prev, u]));
        }
      };

      sock.on("message", onMessage);

      // manejar eventos de estado (join/leave)
      const onStatus = (d: any) => {
        if (!mounted) return;
        const msg = d && d.msg ? d.msg : "";
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
        } catch (e) {}
      };

      sock.on("status", onStatus);

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
          const r = d.room;
          if (r && String(r) !== String(room)) return;
          if (username) setUsersOnline((prev) => prev.filter((x) => x !== username));
        } catch (e) {}
      };

      sock.on("user_joined", onUserJoined);
      sock.on("user_left", onUserLeft);
      sock.on("user_disconnected", onUserDisconnected);

      // Manejar error de PIN inválido
      const onJoinError = (d: any) => {
        if (!mounted) return;
        if (d && d.msg && d.msg.includes("pin inválido")) {
          setPinError("PIN incorrecto. Inténtalo de nuevo.");
          localStorage.removeItem(`pin_${room}`);
          setShowPinDialog(true);
          setPinInput("");
        }
      };
      sock.on("join_error", onJoinError);

      // Si ya hay PIN guardado, unirse automáticamente
      const savedPin = localStorage.getItem(`pin_${room}`);
      if (savedPin) {
        sock.emit("join", { token: token, room, pin: savedPin });
      }

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
        sock.off("join_error", onJoinError);
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

  useEffect(() => {
    // Mueve la vista al 'div' de referencia
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!inputMessage.trim() && !selectedImage && !selectedFile) {
      return;
    }

    const room = id ?? "default";
    const token = localStorage.getItem("chat_token");
    const username = localStorage.getItem("chat_user") || "anonymous";

    try {
      let fileUrl: string | undefined;
      let originalFilename: string | undefined;

      // Si hay imagen o archivo, subirlo primero
      if ((selectedImage || selectedFile) && roomType === "multimedia") {
        const { apiUrl } = await import("@/lib/socket");

        if (selectedImage) {
          // Convertir base64 a blob
          const response = await fetch(selectedImage);
          const blob = await response.blob();
          const formData = new FormData();
          formData.append("file", blob, "image.png");
          formData.append("username", username);

          const uploadResp = await fetch(`${apiUrl}/upload`, {
            method: "POST",
            headers: {
              "Authorization": `Bearer ${token}`,
            },
            body: formData,
          });

          if (uploadResp.ok) {
            const uploadData = await uploadResp.json();
            fileUrl = uploadData.url;
            originalFilename = uploadData.filename;
          } else {
            toast({
              title: "Error al subir imagen",
              description: "No se pudo subir la imagen a Cloudinary",
              variant: "destructive",
            });
            return;
          }
        } else if (selectedFile) {
          // Convertir base64 a blob
          const response = await fetch(selectedFile.data);
          const blob = await response.blob();
          const formData = new FormData();
          formData.append("file", blob, selectedFile.name);
          formData.append("username", username);

          const uploadResp = await fetch(`${apiUrl}/upload`, {
            method: "POST",
            headers: {
              "Authorization": `Bearer ${token}`,
            },
            body: formData,
          });

          if (uploadResp.ok) {
            const uploadData = await uploadResp.json();
            fileUrl = uploadData.url;
            originalFilename = uploadData.filename;
          } else {
            toast({
              title: "Error al subir archivo",
              description: "No se pudo subir el archivo a Cloudinary",
              variant: "destructive",
            });
            return;
          }
        }
      }

      // Emitir el mensaje con la URL del archivo
      import("@/lib/socket").then(({ getSocket }) => {
        const s = getSocket();
        try {
          s?.emit("send_message", {
            token: token,
            room: room,
            msg: inputMessage,
            file_url: fileUrl,
            original_filename: originalFilename,
          });
        } catch (error) {
          toast({
            title: "Error al enviar mensaje",
            description: "No se pudo enviar el mensaje",
            variant: "destructive",
          });
        }
      });

      setInputMessage("");
      removeSelectedImage();
      removeSelectedFile();
    } catch (error) {
      console.error("Error en handleSendMessage:", error);
      toast({
        title: "Error",
        description: "Ocurrió un error al enviar el mensaje",
        variant: "destructive",
      });
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

  const downloadFile = (fileUrl: string, fileName: string) => {
    if (fileUrl.startsWith('http://') || fileUrl.startsWith('https://')) {
      // Usar el proxy del backend para evitar CORS
      const backendUrl = (import.meta.env.VITE_API_URL as string) || "http://localhost:5000";
      const proxyUrl = `${backendUrl}/download?url=${encodeURIComponent(fileUrl)}&filename=${encodeURIComponent(fileName)}`;
      
      console.log("[download] Proxy URL:", proxyUrl);
      
      // Descargar a través del proxy
      const link = document.createElement("a");
      link.href = proxyUrl;
      link.download = fileName;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      
      toast({
        title: "Descargando...",
        description: `${fileName} se está descargando`,
      });
    } else {
      // Para datos base64
      const link = document.createElement("a");
      link.href = fileUrl;
      link.download = fileName;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      
      toast({
        title: "Archivo descargado",
        description: `${fileName} se descargó correctamente`,
      });
    }
  };

  return (
    <div className="h-screen flex flex-col bg-background">
      {/* PIN Dialog */}
      {showPinDialog && (
  <div className="fixed inset-0 flex items-center justify-center z-50 bg-black/30">
    <div className="bg-card p-8 rounded-xl shadow-xl max-w-sm w-full border-2 border-primary flex flex-col items-center">
      <h2 className="text-xl font-bold mb-4 text-primary">Ingresa el PIN de la sala</h2>
      <Input
        type="text"
        placeholder="PIN"
        value={pinInput}
        onChange={e => setPinInput(e.target.value)}
        className="mb-2"
        maxLength={6}
      />
      {pinError && <p className="text-destructive text-sm mb-2">{pinError}</p>}
      <div className="flex gap-2 w-full mt-2">
        <Button
          className="flex-1 bg-primary text-primary-foreground"
          onClick={() => {
            // Validar el PIN
            if (!pinInput || pinInput.length < 4) {
              setPinError("El PIN debe tener al menos 4 dígitos");
              return;
            }

            const token = localStorage.getItem("chat_token");

            // Guardar el PIN
            localStorage.setItem(`pin_${room}`, pinInput);
            setPinError("");

            // Cerrar el diálogo
            setShowPinDialog(false);

            // Emitir el join con el PIN
            import("@/lib/socket").then(({ getSocket }) => {
              const s = getSocket();
              if (s) {
                s.emit("join", {
                  token: token,
                  room: room,
                  pin: pinInput,
                });
              }
            });
          }}
        >
          Entrar
        </Button>
        <Button
          variant="outline"
          className="flex-1 border-primary text-primary"
          onClick={() => {
            setShowPinDialog(false);
            navigate("/lobby");
          }}
        >
          Regresar
        </Button>
      </div>
    </div>
  </div>
)}

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
            <p className="text-xs text-muted-foreground mt-1">Tipo de sala: <span className="font-semibold">{roomType === "multimedia" ? "Multimedia" : "Solo texto"}</span></p>
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
                  {message.image && roomType === "multimedia" && (
                    <div className="mb-2 relative group">
                      <img src={message.image} alt="Imagen compartida" className="max-w-xs rounded-lg cursor-pointer hover:opacity-80 transition" onClick={() => window.open(message.image, '_blank')} />
                      <div className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition flex gap-1">
                        <Button
                          size="sm"
                          className="h-8 w-8 p-0 bg-black/60 hover:bg-black/80"
                          onClick={() => window.open(message.image, '_blank')}
                          title="Abrir en nueva pestaña"
                        >
                          <ExternalLink className="w-3 h-3" />
                        </Button>
                        <Button
                          size="sm"
                          className="h-8 w-8 p-0 bg-black/60 hover:bg-black/80"
                          onClick={() => downloadFile(message.image!, `imagen-${Date.now()}.png`)}
                          title="Descargar imagen"
                        >
                          <Download className="w-3 h-3" />
                        </Button>
                      </div>
                    </div>
                  )}
                  {message.file && roomType === "multimedia" && (
                    <div className="flex items-center gap-2 mb-2 bg-secondary/20 p-2 rounded hover:bg-secondary/30 transition">
                      <FileText className="w-4 h-4 flex-shrink-0" />
                      <span className="text-sm truncate flex-1 cursor-pointer" onClick={() => window.open(message.file!.data, '_blank')} title="Click para abrir en nueva pestaña">
                        {message.file.name}
                      </span>
                      <Button
                        size="sm"
                        variant="ghost"
                        className="p-1 h-6 w-6 hover:bg-primary/20"
                        onClick={() => window.open(message.file!.data, '_blank')}
                        title="Abrir en nueva pestaña"
                      >
                        <ExternalLink className="w-3 h-3" />
                      </Button>
                      <Button
                        size="sm"
                        variant="ghost"
                        className="p-1 h-6 w-6 hover:bg-primary/20"
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
          <div ref={bottomRef} />
        </div>
      </ScrollArea>

      <div className="border-t border-border bg-card/50 backdrop-blur-sm">
        {/* Solo permitir enviar imágenes/archivos si la sala es multimedia */}
        <form onSubmit={handleSendMessage} className="container mx-auto max-w-4xl px-4 py-4 space-y-3">
          {selectedImage && roomType === "multimedia" && (
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
          {selectedFile && roomType === "multimedia" && (
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
            {roomType === "multimedia" && (
              <>
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
              </>
            )}
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
