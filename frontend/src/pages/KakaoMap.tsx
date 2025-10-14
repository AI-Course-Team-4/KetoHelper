import { useEffect, useRef } from "react";


type KakaoMapProps = {
  lat?: number;
  lng?: number;
  initialLevel?: number;
  height?: number | string;
  markers?: { lat: number; lng: number; title?: string; phone?: string }[];
  markerSize?: number; // px
  onMarkerClick?: (payload: { index: number; lat: number; lng: number; title?: string; }) => void;
  onLoaded?: () => void;
  // 레스토랑 데이터로 마커를 찍고 싶을 때 사용 (lat/lng 없으면 address로 지오코딩)
  restaurants?: Array<{
    id: string;
    name: string;
    address: string;
    lat?: number;
    lng?: number;
  }>;
  /** true면 마커/식당을 모두 화면에 보이도록 자동으로 맞춤 */
  fitToBounds?: boolean;
  /** 별도로 강조할 마커 (예: 강남역) */
  specialMarker?: { lat: number; lng: number; title?: string };
  /** 외부(리스트)에서 선택된 인덱스가 바뀌면 해당 마커 말풍선을 열어줌 */
  activeIndex?: number | null;
};


const KakaoMap: React.FC<KakaoMapProps> = ({
  lat,
  lng,
  initialLevel = 5,
  height = '100%',
  markerSize = 64,
  onMarkerClick,
  onLoaded,
  markers,
  restaurants,
  fitToBounds = true,
  specialMarker,
  activeIndex,
}) => {
  const DEFAULT_LAT = lat;
  const DEFAULT_LNG = lng;
  const isMarkerClickRef = useRef(false);
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<any>(null);
  const mapIdRef = useRef<string>(`map-${Math.random().toString(36).substr(2, 9)}`);
  const createdMarkersRef = useRef<any[]>([]);
  const createdOverlaysRef = useRef<any[]>([]);
  const openedOverlayRef = useRef<any>(null);
  const openedOverlayKeyRef = useRef<string | null>(null);
  const overlayByKeyRef = useRef<Map<string, any>>(new Map());
  const markerByKeyRef = useRef<Map<string, any>>(new Map());
  const selectedMarkerKeyRef = useRef<string | null>(null);

  // 위/경도로 주소 역지오코딩
  const reverseGeocode = (plat: number, plng: number): Promise<string | null> => {
    return new Promise((resolve) => {
      if (!(window as any).kakao?.maps?.services?.Geocoder) {
        resolve(null);
        return;
      }
      const geocoder = new window.kakao.maps.services.Geocoder();
      geocoder.coord2Address(plng, plat, (result: any[], status: string) => {
        if (status === window.kakao.maps.services.Status.OK && result[0]) {
          const road = result[0].road_address?.address_name;
          const jibun = result[0].address?.address_name;
          resolve(road || jibun || null);
        } else {
          resolve(null);
        }
      });
    });
  };

  // 거리 계산 (haversine)
  // const toRad = (v: number) => (v * Math.PI) / 180;
  // const distanceMeters = (aLat: number, aLng: number, bLat: number, bLng: number): number => {
  //   const R = 6371000; // meters
  //   const dLat = toRad(bLat - aLat);
  //   const dLng = toRad(bLng - aLng);
  //   const lat1 = toRad(aLat);
  //   const lat2 = toRad(bLat);
  //   const sinDLat = Math.sin(dLat / 2);
  //   const sinDLng = Math.sin(dLng / 2);
  //   const a = sinDLat * sinDLat + Math.cos(lat1) * Math.cos(lat2) * sinDLng * sinDLng;
  //   const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  //   return R * c;
  // };
  // const formatDistance = (m: number): string => (m < 1000 ? `${Math.round(m)}m` : `${(m / 1000).toFixed(1)}km`);

  // 마커/오버레이 재구성 함수: 지도는 재생성하지 않고 현재 데이터만 반영
  const rebuildMarkers = async () => {
    const map = mapRef.current;
    if (!map || !(window as any).kakao) return;

    // 현재 열린 오버레이가 있다면 먼저 닫아 중복 표시 방지
    if (openedOverlayRef.current) {
      openedOverlayRef.current.setMap(null);
      openedOverlayRef.current = null;
      // 키는 유지하여 아래에서 동일 위치 오버레이를 새로 열어 복원
    }

    // 기존 마커/오버레이 제거
    createdMarkersRef.current.forEach(m => m.setMap(null));
    createdOverlaysRef.current.forEach(o => o.setMap(null));
    createdMarkersRef.current = [];
    createdOverlaysRef.current = [];
    overlayByKeyRef.current.clear();
    markerByKeyRef.current.clear();
    selectedMarkerKeyRef.current = null;

    const imageSize = new window.kakao.maps.Size(markerSize, markerSize);
    const imageOffset = new window.kakao.maps.Point(Math.floor(markerSize / 2), markerSize);

    // SVG 이미지 준비
    const svgGreen = `<?xml version="1.0" encoding="UTF-8"?>\n<svg xmlns="http://www.w3.org/2000/svg" width="${markerSize}" height="${markerSize}" viewBox="0 0 24 24">\n  <path fill="#4caf50" d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5S10.62 6.5 12 6.5s2.5 1.12 2.5 2.5S13.38 11.5 12 11.5z"/>\n  <circle cx="12" cy="9.5" r="3" fill="#ffffff"/>\n</svg>`;
    const svgBlue = `<?xml version="1.0" encoding="UTF-8"?>\n<svg xmlns="http://www.w3.org/2000/svg" width="${markerSize}" height="${markerSize}" viewBox="0 0 24 24">\n  <path fill="#1e88e5" d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5S10.62 6.5 12 6.5s2.5 1.12 2.5 2.5S13.38 11.5 12 11.5z"/>\n  <circle cx="12" cy="9.5" r="3" fill="#ffffff"/>\n</svg>`;
    const markerImageGreen = new window.kakao.maps.MarkerImage(
      'data:image/svg+xml;charset=UTF-8,' + encodeURIComponent(svgGreen),
      imageSize,
      { offset: imageOffset }
    );
    const markerImageBlue = new window.kakao.maps.MarkerImage(
      'data:image/svg+xml;charset=UTF-8,' + encodeURIComponent(svgBlue),
      imageSize,
      { offset: imageOffset }
    );

    // 포지션 수집 (레스토랑/마커)
    let positions: Array<{ lat: number; lng: number; title?: string; address?: string; originalIndex?: number; distanceKm?: number; }> = [];
    if (restaurants && restaurants.length > 0) {
      const hasMissing = restaurants.some(r => typeof r.lat !== 'number' || typeof r.lng !== 'number');
      if (!hasMissing) {
        positions = restaurants.map((r: any, i) => ({ lat: r.lat as number, lng: r.lng as number, title: r.name, address: r.address, originalIndex: i, distanceKm: typeof r.distance_km === 'number' ? r.distance_km : undefined }));
      } else if ((window as any).kakao?.maps?.services?.Geocoder) {
        const geocoder = new window.kakao.maps.services.Geocoder();
        const geocodeOne = (addr: string) => new Promise<{ lat?: number; lng?: number }>((resolve) => {
          geocoder.addressSearch(addr, (result: any[], status: string) => {
            if (status === window.kakao.maps.services.Status.OK && result[0]) {
              resolve({ lat: parseFloat(result[0].y), lng: parseFloat(result[0].x) });
            } else {
              resolve({});
            }
          });
        });
        for (let i = 0; i < restaurants.length; i++) {
          const r: any = restaurants[i];
          let coord = { lat: r.lat, lng: r.lng } as { lat?: number; lng?: number };
          if (typeof coord.lat !== 'number' || typeof coord.lng !== 'number') {
            const geo = await geocodeOne(r.address);
            coord = geo;
          }
          if (typeof coord.lat === 'number' && typeof coord.lng === 'number') {
            positions.push({ lat: coord.lat!, lng: coord.lng!, title: r.name, address: r.address, originalIndex: i, distanceKm: typeof r.distance_km === 'number' ? r.distance_km : undefined });
          }
        }
      } else {
        positions = (restaurants as any[])
          .filter(r => typeof r.lat === 'number' && typeof r.lng === 'number')
          .map((r, i) => ({ lat: r.lat as number, lng: r.lng as number, title: r.name, address: r.address, originalIndex: i, distanceKm: typeof r.distance_km === 'number' ? r.distance_km : undefined }));
      }
    } else if (Array.isArray(markers) && markers.length > 0) {
      positions = markers.map(m => ({ lat: m.lat, lng: m.lng, title: m.title }));
    } else {
      if (lat === DEFAULT_LAT && lng === DEFAULT_LNG) {
        positions = [{ lat: lat as number, lng: lng as number, title: '강남역', address: '서울특별시 강남구 강남대로 지하396 (역삼동 858)' }];
      } else {
        positions = [{ lat: lat as number, lng: lng as number }];
      }
    }

    // 좌표 키로 중복 제거 (레스토랑/markers 양쪽에서 중복될 수 있음)
    const seen = new Set<string>();
    positions = positions.filter(p => {
      const key = `${p.lat.toFixed(6)},${p.lng.toFixed(6)}`;
      if (seen.has(key)) return false;
      seen.add(key);
      return true;
    });

    // 마커/오버레이 생성
    positions.forEach((pos) => {
      const key = `${pos.lat.toFixed(6)},${pos.lng.toFixed(6)}`;
      const isSpecial = (
        !!specialMarker && Math.abs(pos.lat - specialMarker.lat) < 1e-6 && Math.abs(pos.lng - specialMarker.lng) < 1e-6
      ) || ((pos as any).title === '강남역');
      const marker = new window.kakao.maps.Marker({
        position: new window.kakao.maps.LatLng(pos.lat, pos.lng),
        title: (pos as any).title,
        image: isSpecial ? markerImageBlue : markerImageGreen,
      });
      marker.setMap(map);
      createdMarkersRef.current.push(marker);
      markerByKeyRef.current.set(key, marker);

      if ((pos as any).title) {
        const labelHtml = `
          <span
            style="
              display: inline-block;
              pointer-events: none;
              white-space: nowrap;
              padding: 2px 6px;
              font-size: 11px;
              font-weight: 800;
              color: #000000;
              text-shadow: -1px 0 white, 0 1px white, 1px 0 white, 0 -1px white;
              transform: translate(0, -12px);
            "
          >
            ${(pos as any).title}
          </span>`;
        const labelOverlay = new window.kakao.maps.CustomOverlay({
          position: new window.kakao.maps.LatLng(pos.lat, pos.lng),
          content: labelHtml,
          yAnchor: 0,
          xAnchor: 0.5,
          zIndex: 2,
        });
        labelOverlay.setMap(map);
        createdOverlaysRef.current.push(labelOverlay);
      }

      // 거리 표기 비활성화 (프런트 계산/표기 주석 처리)
      let distanceHtml = '';
      // if (typeof (pos as any).distanceKm === 'number') {
      //   const km = (pos as any).distanceKm as number
      //   const text = km < 1 ? `${Math.round(km * 1000)}m` : `${km.toFixed(1)}km`
      //   distanceHtml = `<div style=\"color:#616161;\">거리: ${text}</div>`
      // } else if (specialMarker && typeof specialMarker.lat === 'number' && typeof specialMarker.lng === 'number') {
      //   const d = distanceMeters(specialMarker.lat, specialMarker.lng, pos.lat, pos.lng)
      //   distanceHtml = `<div style=\"color:#616161;\">거리: ${formatDistance(d)}</div>`
      // }

      const contentHtml = `
        <div style="position:relative;pointer-events:auto;">
          <div style="
            background:#ffffff;
            border-radius:12px;
            box-shadow:0 12px 32px rgba(0,0,0,0.3);
            border:1px solid #ddd;
            white-space:nowrap;
            min-width:200px;
            overflow:hidden;
          ">
            <div style="padding:12px 14px;font-size:13px;color:#212121;">
              <div style="font-weight:700;margin-bottom:6px;">
                ${(pos as any).title || ''}
              </div>
              ${`<div style=\"color:#616161;\">${(pos as any).address}</div>`}
              <b>${distanceHtml}</b>
            </div>
          </div>
          <div style="
            position:absolute;left:50%;bottom:-7px;transform:translateX(-50%);
            width:0;height:0;border-left:10px solid transparent;border-right:10px solid transparent;border-top:10px solid #fff;
            z-index:10;
          "></div>
          <div style="
            position:absolute;left:50%;bottom:-5px;transform:translateX(-50%);
            width:0;height:0;border-left:9px solid transparent;border-right:9px solid transparent;border-top:9px solid #ffffff;
            z-index:11;
          "></div>
        </div>`;

      const overlay = new window.kakao.maps.CustomOverlay({
        position: new window.kakao.maps.LatLng(pos.lat, pos.lng),
        content: contentHtml,
        yAnchor: 1.8,
        xAnchor: 0.5,
        zIndex: 10000,
      });
      overlayByKeyRef.current.set(key, overlay);

      window.kakao.maps.event.addListener(marker, 'click', () => {
        isMarkerClickRef.current = true;

        // 다른 오버레이가 열려 있으면 닫기
        if (openedOverlayRef.current && openedOverlayKeyRef.current !== key) {
          openedOverlayRef.current.setMap(null);
          openedOverlayRef.current = null;
          openedOverlayKeyRef.current = null;
        }
        // 같은 오버레이면 재설정하지 않음
        if (openedOverlayKeyRef.current !== key) {
          overlay.setMap(map);
          openedOverlayRef.current = overlay;
          openedOverlayKeyRef.current = key;
        }
        // 짧은 지연 후 플래그 해제하여 이후 지도 상호작용 시 닫히도록 함
        setTimeout(() => {
          isMarkerClickRef.current = false;
        }, 150);

        if (onMarkerClick) {
          const listIndex = typeof pos.originalIndex === 'number' ? pos.originalIndex : -1;
          onMarkerClick({ index: listIndex, lat: pos.lat, lng: pos.lng, title: (pos as any).title });
        }
      });
    });

    if (fitToBounds && positions.length > 0 && (restaurants?.length || markers?.length)) {
      const bounds = new window.kakao.maps.LatLngBounds();
      positions.forEach(p => bounds.extend(new window.kakao.maps.LatLng(p.lat, p.lng)));
      map.setBounds(bounds);
    }

    // 이미 열려있던 오버레이 복원 (중복 방지: 위에서 모두 닫은 상태이므로 한 개만 복원)
    if (openedOverlayKeyRef.current) {
      const existing = overlayByKeyRef.current.get(openedOverlayKeyRef.current);
      if (existing) {
        existing.setMap(map);
        openedOverlayRef.current = existing;
      } else {
        openedOverlayKeyRef.current = null;
      }
    }

    // 별도 강조 마커 처리
    if (specialMarker && typeof specialMarker.lat === 'number' && typeof specialMarker.lng === 'number') {
      // 기본 위치(특별 마커)는 항상 파란색으로 유지하고, 목록 마커와 겹치더라도 별도로 표시
      const sm = new window.kakao.maps.Marker({
        position: new window.kakao.maps.LatLng(specialMarker.lat, specialMarker.lng),
        title: specialMarker.title,
        image: markerImageBlue,
        zIndex: 1000,
      });
      sm.setMap(map);
      createdMarkersRef.current.push(sm);

      // 기본 위치 제목 라벨 (예: 강남역) - 마커 위 ("현재 위치" 텍스트는 제외)
      if (specialMarker.title && specialMarker.title !== '현재 위치') {
        const titleLabelHtml = `
          <span
            style="
              display: inline-block;
              pointer-events: none;
              white-space: nowrap;
              padding: 2px 6px;
              font-size: 11px;
              font-weight: 800;
              color: #000000;
              text-shadow: -1px 0 white, 0 1px white, 1px 0 white, 0 -1px white;
              transform: translate(0, -12px);
            "
          >
            ${specialMarker.title}
          </span>`;
        const titleLabelOverlay = new window.kakao.maps.CustomOverlay({
          position: new window.kakao.maps.LatLng(specialMarker.lat, specialMarker.lng),
          content: titleLabelHtml,
          yAnchor: 0,
          xAnchor: 0.5,
          zIndex: 1002,
        });
        titleLabelOverlay.setMap(map);
        createdOverlaysRef.current.push(titleLabelOverlay);
      }

      // 기본 위치 클릭 시 주소 말풍선과 동일한 오버레이 열기 (역지오코딩 포함)
      const specialOverlay = new window.kakao.maps.CustomOverlay({
        position: new window.kakao.maps.LatLng(specialMarker.lat, specialMarker.lng),
        content: '',
        yAnchor: 1.8,
        xAnchor: 0.5,
        zIndex: 10020,
      });

      window.kakao.maps.event.addListener(sm, 'click', async () => {
        isMarkerClickRef.current = true;

        const addr = await reverseGeocode(specialMarker.lat, specialMarker.lng);
        const html = `
          <div style="position:relative;pointer-events:auto;">
            <div style="
              background:#ffffff;
              border-radius:12px;
              box-shadow:0 12px 32px rgba(0,0,0,0.3);
              border:1px solid #ddd;
              white-space:nowrap;
              min-width:200px;
              overflow:hidden;
            ">
              <div style="padding:12px 14px;font-size:13px;color:#212121;">
                <div style="font-weight:700;margin-bottom:6px;">
                  ${specialMarker.title || ''}
                </div>
                <div style="color:#616161;">${addr ?? `위도: ${(specialMarker.lat).toFixed(6)}, 경도: ${(specialMarker.lng).toFixed(6)}`}</div>
              </div>
            </div>
            <div style="
              position:absolute;left:50%;bottom:-7px;transform:translateX(-50%);
              width:0;height:0;border-left:10px solid transparent;border-right:10px solid transparent;border-top:10px solid #fff;
              z-index:10;
            "></div>
            <div style="
              position:absolute;left:50%;bottom:-5px;transform:translateX(-50%);
              width:0;height:0;border-left:9px solid transparent;border-right:9px solid transparent;border-top:9px solid #ffffff;
              z-index:11;
            "></div>
          </div>`;

        // 다른 오버레이 닫기
        if (openedOverlayRef.current && openedOverlayKeyRef.current !== 'special') {
          openedOverlayRef.current.setMap(null);
          openedOverlayRef.current = null;
          openedOverlayKeyRef.current = null;
        }
        // 콘텐츠 설정 및 열기
        specialOverlay.setContent(html);
        specialOverlay.setMap(map);
        openedOverlayRef.current = specialOverlay;
        openedOverlayKeyRef.current = 'special';

        setTimeout(() => { isMarkerClickRef.current = false; }, 150);
      });
    }

    // 마커/오버레이 생성이 완료된 시점에 로딩 완료 콜백 호출
    try {
      if (typeof onLoaded === 'function') {
        onLoaded();
      }
    } catch {}
  };

  useEffect(() => {
    if (!import.meta.env.VITE_KAKAO_MAP_JSKEY) {
      console.error("VITE_KAKAO_MAP_JSKEY 가 설정되지 않았습니다.");
      return;
    }


    const initMap = () => {
      if (!(window as any).kakao?.maps?.load) return;
      window.kakao.maps.load(async () => {
        const container = containerRef.current ?? document.getElementById(mapIdRef.current);
        if (!container) return;


        // 지도 옵션
        const options = {
          center: new window.kakao.maps.LatLng(lat, lng),
          level: initialLevel,
        };
        const map = new window.kakao.maps.Map(container, options);
        // 초기 레벨은 최초 1회만 적용(상태 초기값처럼 동작)
        
        mapRef.current = map;
        // 초기 1회: 맵 클릭시 닫기만 설정, 마커/오버레이는 별도 함수로 구성


        // 최초 로드시 마커/오버레이 구성
        await rebuildMarkers();

        // 타일 렌더 완료 이벤트에서 한 번 더 보장적으로 콜백 호출
        try {
          if (typeof onLoaded === 'function') {
            const once = () => {
              onLoaded();
              window.kakao.maps.event.removeListener(map, 'tilesloaded', once);
            };
            window.kakao.maps.event.addListener(map, 'tilesloaded', once);
          }
        } catch {}


        // 맵 상호작용 시 열린 말풍선 닫기 (마커 클릭 직후는 예외)
        const closeIfOpen = () => {
          if (isMarkerClickRef.current) return;
          if (openedOverlayRef.current) {
            openedOverlayRef.current.setMap(null);
            openedOverlayRef.current = null;
            openedOverlayKeyRef.current = null;
          }
        };
        window.kakao.maps.event.addListener(map, 'click', closeIfOpen);
        window.kakao.maps.event.addListener(map, 'rightclick', closeIfOpen);
        window.kakao.maps.event.addListener(map, 'dragstart', closeIfOpen);
        window.kakao.maps.event.addListener(map, 'zoom_changed', closeIfOpen);
        
      });
    };


    if ((window as any).kakao && (window as any).kakao.maps) {
      initMap();
      return;
    }


    // SDK 스크립트 로드 (지오코딩을 위해 services 라이브러리 포함)
    const id = "kakao-maps-sdk";
    let script = document.getElementById(id) as HTMLScriptElement | null;
    if (!script) {
      script = document.createElement("script");
      script.id = id;
      script.async = true;
      script.src = `https://dapi.kakao.com/v2/maps/sdk.js?appkey=${import.meta.env.VITE_KAKAO_MAP_JSKEY}&autoload=false&libraries=services`;
      document.head.appendChild(script);
    }
    script.addEventListener("load", initMap);


    return () => {
      script?.removeEventListener("load", initMap);
      createdMarkersRef.current.forEach((m) => m.setMap(null));
      createdOverlaysRef.current.forEach((o) => o.setMap(null));
      overlayByKeyRef.current.clear();
      markerByKeyRef.current.clear();
      openedOverlayRef.current = null;
      openedOverlayKeyRef.current = null;
      selectedMarkerKeyRef.current = null;
    };
    // 데이터 변경 시 마커/오버레이만 갱신
  }, [lat, lng]);

  useEffect(() => {
    // 지도 생성 이후에만 갱신
    if (!mapRef.current) return;
    rebuildMarkers();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [markers, markerSize, restaurants, fitToBounds, specialMarker]);

  // (초기 레벨만 적용하므로 이후 변경은 반영하지 않음)

  // 외부에서 선택된 인덱스를 받아 해당 말풍선을 열고 마커 색상을 노란색으로 변경
  useEffect(() => {
    const map = mapRef.current
    if (!map) return
    if (typeof activeIndex !== 'number' || !restaurants || activeIndex < 0 || activeIndex >= restaurants.length) return
    const r = restaurants[activeIndex]
    if (typeof r?.lat !== 'number' || typeof r?.lng !== 'number') return
    const key = `${r.lat.toFixed(6)},${r.lng.toFixed(6)}`
    const overlay = overlayByKeyRef.current.get(key)
    if (!overlay) return
    if (openedOverlayRef.current && openedOverlayKeyRef.current !== key) {
      openedOverlayRef.current.setMap(null)
    }
    overlay.setMap(map)
    openedOverlayRef.current = overlay
    openedOverlayKeyRef.current = key
    // 선택된 아이템 위치로 지도 부드럽게 이동
    map.panTo(new window.kakao.maps.LatLng(r.lat, r.lng))

    // 마커 색상 업데이트: 이전 선택 마커 원복, 현재 선택 마커는 노란색
    const specialKey = specialMarker ? `${specialMarker.lat.toFixed(6)},${specialMarker.lng.toFixed(6)}` : null
    const prevKey = selectedMarkerKeyRef.current
    if (prevKey && markerByKeyRef.current.has(prevKey)) {
      const prevMarker = markerByKeyRef.current.get(prevKey)
      if (specialKey && prevKey === specialKey) {
        // 이전이 특별 마커였으면 파란색 복원
        // 파란 마커 이미지는 rebuildMarkers 스코프 내에 있으므로, 동일 로직으로 대체 불가 -> 간단히 녹색으로 복원 후 특별 마커는 별도 분기에서 항상 파란색 생성됨
        // 안전하게 녹색으로 복원
        prevMarker.setImage(markerByKeyRef.current.get(prevKey)?.getImage() || null)
      }
    }
    // 모든 마커의 기본 이미지 복원 대신, 이전 선택만 복원
    if (prevKey && markerByKeyRef.current.has(prevKey)) {
      const prevMarker = markerByKeyRef.current.get(prevKey)
      if (specialKey && prevKey === specialKey) {
        // 특별 마커는 파란색
        prevMarker.setImage(new window.kakao.maps.MarkerImage(
          'data:image/svg+xml;charset=UTF-8,' + encodeURIComponent(`<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"${markerSize}\" height=\"${markerSize}\" viewBox=\"0 0 24 24\">\n  <path fill=\"#1e88e5\" d=\"M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5S10.62 6.5 12 6.5s2.5 1.12 2.5 2.5S13.38 11.5 12 11.5z\"/>\n  <circle cx=\"12\" cy=\"9.5\" r=\"3\" fill=\"#ffffff\"/>\n</svg>`),
          new window.kakao.maps.Size(markerSize, markerSize),
          { offset: new window.kakao.maps.Point(Math.floor(markerSize / 2), markerSize) }
        ))
      } else {
        // 일반 마커는 녹색
        prevMarker.setImage(new window.kakao.maps.MarkerImage(
          'data:image/svg+xml;charset=UTF-8,' + encodeURIComponent(`<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"${markerSize}\" height=\"${markerSize}\" viewBox=\"0 0 24 24\">\n  <path fill=\"#4caf50\" d=\"M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5S10.62 6.5 12 6.5s2.5 1.12 2.5 2.5S13.38 11.5 12 11.5z\"/>\n  <circle cx=\"12\" cy=\"9.5\" r=\"3\" fill=\"#ffffff\"/>\n</svg>`),
          new window.kakao.maps.Size(markerSize, markerSize),
          { offset: new window.kakao.maps.Point(Math.floor(markerSize / 2), markerSize) }
        ))
      }
    }

    // 현재 선택 마커를 노란색으로 설정
    const curMarker = markerByKeyRef.current.get(key)
    if (curMarker) {
      curMarker.setImage(new window.kakao.maps.MarkerImage(
        'data:image/svg+xml;charset=UTF-8,' + encodeURIComponent(`<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"${markerSize}\" height=\"${markerSize}\" viewBox=\"0 0 24 24\">\n  <path fill=\"#fbc02d\" d=\"M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5S10.62 6.5 12 6.5s2.5 1.12 2.5 2.5S13.38 11.5 12 11.5z\"/>\n  <circle cx=\"12\" cy=\"9.5\" r=\"3\" fill=\"#ffffff\"/>\n</svg>`),
        new window.kakao.maps.Size(markerSize, markerSize),
        { offset: new window.kakao.maps.Point(Math.floor(markerSize / 2), markerSize) }
      ))
      selectedMarkerKeyRef.current = key
    }
  }, [activeIndex, restaurants, specialMarker, markerSize])


  const resolvedHeight = typeof height === 'number' ? `${height}px` : height;


  return <div ref={containerRef} id={mapIdRef.current} style={{ width: "100%", height: resolvedHeight }} />;
};


export default KakaoMap;