import { useEffect, useState } from "react";
import { Box, Typography } from "@mui/material";

type KakaoMapProps = {
  lat?: number;
  lng?: number;
  level?: number;
  height?: number | string;
};

const KakaoMap: React.FC<KakaoMapProps> = ({
  lat = 37.5665,
  lng = 126.9780,
  level = 2,
  height = '100%',
}) => {
  const [mapError, setMapError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    if (!import.meta.env.VITE_KAKAO_MAP_JSKEY) {
      console.error("VITE_KAKAO_MAP_JSKEY 가 설정되지 않았습니다.");
      setMapError("카카오 맵 API 키가 설정되지 않았습니다.");
      setIsLoading(false);
      return;
    }

    const initMap = () => {
      try {
        if (!(window as any).kakao?.maps?.load) {
          setMapError("카카오 맵 SDK가 로드되지 않았습니다.");
          setIsLoading(false);
          return;
        }
        
        // @ts-ignore
        window.kakao.maps.load(() => {
          const container = document.getElementById("map");
          if (!container) {
            setMapError("지도 컨테이너를 찾을 수 없습니다.");
            setIsLoading(false);
            return;
          }

          // 지도 옵션
          const options = {
            center: new window.kakao.maps.LatLng(lat, lng),
            level,
          };
          const map = new window.kakao.maps.Map(container, options);

          // 마커
          const marker = new window.kakao.maps.Marker({
            position: new window.kakao.maps.LatLng(lat, lng),
          });
          marker.setMap(map);
          
          setIsLoading(false);
          setMapError(null);
        });
      } catch (error) {
        console.error("지도 초기화 오류:", error);
        setMapError("지도를 로드하는 중 오류가 발생했습니다.");
        setIsLoading(false);
      }
    };

    // 이미 로드된 경우 바로 초기화
    if ((window as any).kakao && (window as any).kakao.maps) {
      initMap();
      return;
    }

    // SDK 스크립트 로드
    const id = "kakao-maps-sdk";
    let script = document.getElementById(id) as HTMLScriptElement | null;
    if (!script) {
      script = document.createElement("script");
      script.id = id;
      script.async = true;
      script.src = `https://dapi.kakao.com/v2/maps/sdk.js?appkey=${import.meta.env.VITE_KAKAO_MAP_JSKEY}&autoload=false`;
      document.head.appendChild(script);
    }
    
    const handleLoad = () => {
      initMap();
    };
    
    const handleError = () => {
      setMapError("카카오 맵 SDK 로드에 실패했습니다.");
      setIsLoading(false);
    };
    
    script.addEventListener("load", handleLoad);
    script.addEventListener("error", handleError);

    return () => {
      script?.removeEventListener("load", handleLoad);
      script?.removeEventListener("error", handleError);
    };
  }, [lat, lng, level]);

  const resolvedHeight = typeof height === 'number' ? `${height}px` : height;
  
  if (mapError) {
    return (
      <Box 
        sx={{ 
          width: "100%", 
          height: resolvedHeight,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          backgroundColor: '#f5f5f5',
          border: '1px solid #ddd',
          borderRadius: 1
        }}
      >
        <Typography variant="body2" color="text.secondary">
          {mapError}
        </Typography>
      </Box>
    );
  }
  
  if (isLoading) {
    return (
      <Box 
        sx={{ 
          width: "100%", 
          height: resolvedHeight,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          backgroundColor: '#f5f5f5',
          border: '1px solid #ddd',
          borderRadius: 1
        }}
      >
        <Typography variant="body2" color="text.secondary">
          지도를 로드하는 중...
        </Typography>
      </Box>
    );
  }
  
  return <div id="map" style={{ width: "100%", height: resolvedHeight }} />;
};

export default KakaoMap;